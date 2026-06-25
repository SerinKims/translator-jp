from __future__ import annotations

import json
import time
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.repositories.chunk_repository import ChunkRepository
from app.db.repositories.translation_repository import TranslationRepository
from app.llm.ollama_client import (
    OLLAMA_EMPTY_RESPONSE_MESSAGE,
    OLLAMA_TIMEOUT_MESSAGE,
    OllamaClient,
    OllamaClientError,
)
from app.llm.prompts import PromptLoader, PromptLoaderError
from app.schemas.translation import (
    TranslationChunkResponse,
    TranslationRequest,
    TranslationResponse,
)
from app.services.chunker import (
    CHUNK_OVERLAP_PARAGRAPHS,
    MAX_CHARS_PER_CHUNK,
    chunk_text,
)


MODEL_NAME = "gemma4:26b-a4b-it-q4_K_M"
PROMPT_VERSION = "translate_ja_ko_v1"

EMPTY_TEXT_MESSAGE = "번역할 텍스트를 입력해주세요."
ONLY_KO_TARGET_MESSAGE = "현재 목표 언어는 한국어만 지원합니다."
OLLAMA_CONNECTION_MESSAGE = (
    "Ollama 서버에 연결할 수 없습니다. 로컬에서 Ollama가 실행 중인지 확인해주세요."
)
MODEL_NOT_FOUND_MESSAGE = (
    "gemma4:26b-a4b-it-q4_K_M 모델을 찾을 수 없습니다. "
    "ollama pull gemma4:26b-a4b-it-q4_K_M 명령어로 모델을 설치해주세요."
)
TRANSLATION_TIMEOUT_MESSAGE = (
    "번역 시간이 너무 오래 걸렸습니다. 입력 문장을 줄이거나 다시 시도해주세요."
)
EMPTY_MODEL_RESPONSE_MESSAGE = "모델이 빈 응답을 반환했습니다. 다시 시도해주세요."
STREAM_NOT_SUPPORTED_MESSAGE = "스트리밍 번역은 아직 지원하지 않습니다."


class TranslationServiceError(RuntimeError):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class TranslationService:
    def __init__(
        self,
        db: Session,
        *,
        ollama_client: Any | None = None,
        prompt_loader: PromptLoader | None = None,
        max_chars_per_chunk: int | None = None,
        chunk_overlap_paragraphs: int | None = None,
    ) -> None:
        settings = get_settings()
        self.db = db
        self.ollama_client = ollama_client or OllamaClient()
        self.prompt_loader = prompt_loader or PromptLoader()
        self.max_chars_per_chunk = (
            max_chars_per_chunk or settings.max_chars_per_chunk or MAX_CHARS_PER_CHUNK
        )
        self.chunk_overlap_paragraphs = (
            chunk_overlap_paragraphs
            if chunk_overlap_paragraphs is not None
            else settings.chunk_overlap_paragraphs or CHUNK_OVERLAP_PARAGRAPHS
        )
        self.model_name = settings.ollama_model_name or MODEL_NAME
        self.prompt_version = settings.prompt_version or PROMPT_VERSION

    async def translate_text(self, request: TranslationRequest) -> TranslationResponse:
        started_at = time.perf_counter()
        self._validate_request(request)

        prompt_version = self.prompt_loader.select_prompt_version(
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            prompt_version=self.prompt_version,
        )
        system_prompt = self.prompt_loader.load(
            prompt_version,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
        )

        translation_repository = TranslationRepository(self.db)
        chunk_repository = ChunkRepository(self.db)
        job = translation_repository.create_job(
            original_text=request.text,
            source_language=request.source_lang,
            target_language=request.target_lang,
            source_site="manual",
            source_url=None,
            source_title=None,
            source_author=None,
            source_work_id=None,
            source_fetched_at=None,
            model_name=self.model_name,
            prompt_version=prompt_version,
            ollama_think=request.think,
            ollama_options=request.options,
            style=request.style,
            honorific_policy=request.honorific_policy,
            preserve_names=request.preserve_names,
            status="running",
        )

        chunks = chunk_text(
            request.text,
            max_chars_per_chunk=self.max_chars_per_chunk,
            overlap_paragraphs=self.chunk_overlap_paragraphs,
        )
        translation_repository.update_job(job.id, total_chunks=len(chunks))

        translated_chunks: list[tuple[int, str]] = []
        chunk_responses: list[TranslationChunkResponse] = []
        failed_messages: list[str] = []

        for chunk in chunks:
            chunk_repository.create_chunk(
                job_id=job.id,
                chunk_index=chunk["index"],
                source_text=chunk["source_text"],
                context_before=chunk["context_before"],
                context_after=chunk["context_after"],
                status="pending",
            )
            chunk_repository.update_status(
                job_id=job.id,
                chunk_index=chunk["index"],
                status="running",
            )

            messages = self._build_messages(
                request=request,
                system_prompt=system_prompt,
                source_text=chunk["source_text"],
                context_before=chunk["context_before"],
                context_after=chunk["context_after"],
            )
            try:
                result = await self.ollama_client.chat(
                    messages,
                    options=request.options,
                    think=request.think,
                )
                translated_text = self._extract_translation_text(result.content)
                if not translated_text:
                    raise OllamaClientError(
                        EMPTY_MODEL_RESPONSE_MESSAGE,
                        code="empty_response",
                    )
                chunk_repository.update_status(
                    job_id=job.id,
                    chunk_index=chunk["index"],
                    status="completed",
                    translated_text=translated_text,
                    raw_model_response=self._serialize_raw_response(result.raw_response),
                    elapsed_ms=result.elapsed_ms,
                )
                translated_chunks.append((chunk["index"], translated_text))
                chunk_responses.append(
                    TranslationChunkResponse(
                        index=chunk["index"],
                        source_lang=request.source_lang,
                        target_lang=request.target_lang,
                        status="completed",
                    )
                )
            except Exception as exc:  # noqa: BLE001
                message = self._map_model_error(exc)
                failed_messages.append(message)
                chunk_repository.update_status(
                    job_id=job.id,
                    chunk_index=chunk["index"],
                    status="failed",
                    error_message=message,
                    increment_retry_count=True,
                )
                chunk_responses.append(
                    TranslationChunkResponse(
                        index=chunk["index"],
                        source_lang=request.source_lang,
                        target_lang=request.target_lang,
                        status="failed",
                    )
                )

        translated_text = self._merge_translated_chunks(translated_chunks)
        completed_count = len(translated_chunks)
        failed_count = len(failed_messages)
        elapsed_ms = self._elapsed_ms(started_at)
        status = self._job_status(completed_count=completed_count, failed_count=failed_count)
        translation_repository.update_job(
            job.id,
            translated_text=translated_text,
            status=status,
            completed_chunks=completed_count,
            failed_chunks=failed_count,
            elapsed_ms=elapsed_ms,
            error_message=failed_messages[0] if failed_messages else None,
        )

        return TranslationResponse(
            job_id=job.id,
            source_type="pasted_text",
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            current_page_index=request.page_index,
            total_pages=1,
            has_next_page=False,
            translated_text=translated_text,
            model=self.model_name,
            prompt_version=prompt_version,
            style=request.style,
            elapsed_ms=elapsed_ms,
            cache_hit=False,
            chunks=sorted(chunk_responses, key=lambda item: item.index),
        )

    def _validate_request(self, request: TranslationRequest) -> None:
        if not request.text.strip():
            raise TranslationServiceError(EMPTY_TEXT_MESSAGE, status_code=400)
        if request.target_lang != "ko":
            raise TranslationServiceError(ONLY_KO_TARGET_MESSAGE, status_code=400)
        if request.stream:
            raise TranslationServiceError(STREAM_NOT_SUPPORTED_MESSAGE, status_code=400)

    def _build_messages(
        self,
        *,
        request: TranslationRequest,
        system_prompt: str,
        source_text: str,
        context_before: str,
        context_after: str,
    ) -> list[dict[str, str]]:
        glossary_context = self._build_glossary_context(
            enabled=request.use_glossary,
            source_text=source_text,
        )
        user_prompt = "\n".join(
            [
                f"source_lang: {request.source_lang}",
                f"target_lang: {request.target_lang}",
                f"style: {request.style}",
                f"honorific_policy: {request.honorific_policy}",
                f"preserve_names: {request.preserve_names}",
                f"context_before:\n{context_before}" if context_before else "context_before:",
                f"context_after:\n{context_after}" if context_after else "context_after:",
                f"glossary:\n{glossary_context}" if glossary_context else "glossary:",
                "source_text:",
                source_text,
            ]
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _build_glossary_context(self, *, enabled: bool, source_text: str) -> str:
        if not enabled or not source_text:
            return ""
        return ""

    def _extract_translation_text(self, raw_text: str) -> str:
        text = raw_text.strip()
        for prefix in ("번역문:", "번역:", "Translation:", "Translated text:"):
            if text.startswith(prefix):
                return text[len(prefix) :].strip()
        return text

    def _merge_translated_chunks(self, translated_chunks: list[tuple[int, str]]) -> str:
        return "\n\n".join(text for _, text in sorted(translated_chunks))

    def _job_status(self, *, completed_count: int, failed_count: int) -> str:
        if failed_count == 0:
            return "completed"
        if completed_count == 0:
            return "failed"
        return "partial_failed"

    def _map_model_error(self, exc: Exception) -> str:
        if isinstance(exc, PromptLoaderError):
            return str(exc)
        if isinstance(exc, OllamaClientError):
            if exc.code == "runtime_unavailable":
                return OLLAMA_CONNECTION_MESSAGE
            if exc.code == "model_not_found":
                return MODEL_NOT_FOUND_MESSAGE
            if exc.code == "timeout" or exc.message == OLLAMA_TIMEOUT_MESSAGE:
                return TRANSLATION_TIMEOUT_MESSAGE
            if exc.code == "empty_response" or exc.message == OLLAMA_EMPTY_RESPONSE_MESSAGE:
                return EMPTY_MODEL_RESPONSE_MESSAGE
            if self._looks_like_connection_error(exc.message):
                return OLLAMA_CONNECTION_MESSAGE
            return exc.message
        if self._looks_like_connection_error(str(exc)):
            return OLLAMA_CONNECTION_MESSAGE
        return str(exc) or exc.__class__.__name__

    def _looks_like_connection_error(self, message: str) -> bool:
        lowered = message.lower()
        return any(
            token in lowered
            for token in (
                "connection refused",
                "connect",
                "connection error",
                "failed to establish",
                "server disconnected",
            )
        )

    def _serialize_raw_response(self, raw_response: Any) -> str:
        try:
            return json.dumps(raw_response, ensure_ascii=False)
        except TypeError:
            return json.dumps({"response": str(raw_response)}, ensure_ascii=False)

    def _elapsed_ms(self, started_at: float) -> int:
        return max(0, round((time.perf_counter() - started_at) * 1000))
