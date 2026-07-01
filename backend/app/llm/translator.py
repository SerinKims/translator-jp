from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import TranslationJob, TranslationPage
from app.db.repositories.chunk_repository import ChunkRepository
from app.db.repositories.page_repository import PageRepository
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
from app.services.cache import (
    TranslationCacheService,
    build_cache_key,
)
from app.services.chunker import (
    CHUNK_OVERLAP_PARAGRAPHS,
    MAX_CHARS_PER_CHUNK,
    chunk_text,
)
from app.services.glossary import (
    SelectedGlossaryTerm,
    build_glossary_context,
    make_selected_glossary_hash,
    select_glossary_terms_for_text,
)

MODEL_NAME = "gemma4:26b-a4b-it-q4_K_M"
PROMPT_VERSION = "translate_ja_ko_v1"
CHUNK_NOT_FOUND_MESSAGE = "Translation chunk not found."
CHUNK_RETRY_NOT_FAILED_MESSAGE = "Only failed chunks can be retried."
CHUNK_RETRY_AMBIGUOUS_MESSAGE = (
    "Multiple failed chunks have the same index. Retry by page is required."
)

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
JOB_NOT_FOUND_MESSAGE = "번역 작업을 찾을 수 없습니다."


@dataclass(frozen=True)
class TranslationRunOptions:
    source_lang: str
    target_lang: str
    style: str
    honorific_policy: str
    preserve_names: bool
    use_glossary: bool
    use_cache: bool
    think: str | bool
    options: dict[str, Any] | None
    stream: bool = False
    translate_scope: str = "first_page"
    page_index: int = 0
    force: bool = False


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
        run_options = TranslationRunOptions(
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            style=request.style,
            honorific_policy=request.honorific_policy,
            preserve_names=request.preserve_names,
            use_glossary=request.use_glossary,
            use_cache=request.use_cache,
            think=request.think,
            options=request.options,
            stream=request.stream,
            translate_scope=request.translate_scope,
            page_index=request.page_index,
        )
        self._validate_run_options(run_options, text=request.text)

        prompt_version = self.prompt_loader.select_prompt_version(
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            prompt_version=self.prompt_version,
        )
        job = TranslationRepository(self.db).create_job(
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

        return await self._translate_job(job=job, run_options=run_options)

    async def translate_job(
        self,
        job_id: int,
        *,
        source_lang: str = "ja",
        target_lang: str = "ko",
        style: str = "webnovel",
        honorific_policy: str = "preserve",
        preserve_names: bool = True,
        use_glossary: bool = True,
        use_cache: bool = True,
        think: str | bool = False,
        options: dict[str, Any] | None = None,
        stream: bool = False,
        translate_scope: str = "first_page",
        page_index: int = 0,
        force: bool = False,
    ) -> TranslationResponse:
        job = TranslationRepository(self.db).get_job(job_id)
        if job is None:
            raise TranslationServiceError(JOB_NOT_FOUND_MESSAGE, status_code=404)

        run_options = TranslationRunOptions(
            source_lang=source_lang,
            target_lang=target_lang,
            style=style,
            honorific_policy=honorific_policy,
            preserve_names=preserve_names,
            use_glossary=use_glossary,
            use_cache=use_cache,
            think=think,
            options=options,
            stream=stream,
            translate_scope=translate_scope,
            page_index=page_index,
            force=force,
        )
        self._validate_run_options(run_options, text=job.original_text)

        return await self._translate_job(job=job, run_options=run_options)

    async def retry_failed_chunk(self, job_id: int, chunk_index: int) -> TranslationResponse:
        started_at = time.perf_counter()
        translation_repository = TranslationRepository(self.db)
        chunk_repository = ChunkRepository(self.db)
        page_repository = PageRepository(self.db)
        cache_service = TranslationCacheService(self.db)

        job = translation_repository.get_job(job_id)
        if job is None:
            raise TranslationServiceError(JOB_NOT_FOUND_MESSAGE, status_code=404)

        matching_chunks = [
            chunk
            for chunk in chunk_repository.list_chunks(job_id=job.id)
            if chunk.chunk_index == chunk_index
        ]
        if not matching_chunks:
            raise TranslationServiceError(CHUNK_NOT_FOUND_MESSAGE, status_code=404)

        failed_chunks = [chunk for chunk in matching_chunks if chunk.status == "failed"]
        if not failed_chunks:
            raise TranslationServiceError(CHUNK_RETRY_NOT_FAILED_MESSAGE, status_code=400)
        if len(failed_chunks) > 1:
            raise TranslationServiceError(CHUNK_RETRY_AMBIGUOUS_MESSAGE, status_code=409)

        chunk = failed_chunks[0]
        page = page_repository.get_page_by_id(chunk.page_id)
        if page is None:
            raise TranslationServiceError(JOB_NOT_FOUND_MESSAGE, status_code=404)

        run_options = self._run_options_from_job(job, page_index=page.page_index)
        self._validate_run_options(run_options, text=chunk.source_text)
        prompt_version = self.prompt_loader.select_prompt_version(
            source_lang=run_options.source_lang,
            target_lang=run_options.target_lang,
            prompt_version=job.prompt_version,
        )
        system_prompt = self.prompt_loader.load(
            prompt_version,
            source_lang=run_options.source_lang,
            target_lang=run_options.target_lang,
        )

        active_glossary_terms = []
        if run_options.use_glossary:
            from app.db.repositories.glossary_repository import GlossaryRepository

            active_glossary_terms = GlossaryRepository(self.db).list_active_terms(
                source_lang=run_options.source_lang,
                target_lang=run_options.target_lang,
            )

        chunk_repository.update_status(
            job_id=job.id,
            page_id=page.id,
            chunk_index=chunk.chunk_index,
            status="running",
            increment_retry_count=True,
            clear_error_message=True,
        )

        cache_hit = False
        failed_messages: list[str] = []
        selected_glossary_terms = select_glossary_terms_for_text(
            chunk.source_text,
            active_glossary_terms,
            source_lang=run_options.source_lang,
            target_lang=run_options.target_lang,
        )
        selected_glossary_hash = make_selected_glossary_hash(selected_glossary_terms)
        cache_key = build_cache_key(
            source_text=chunk.source_text,
            source_lang=run_options.source_lang,
            target_lang=run_options.target_lang,
            model_name=job.model_name,
            prompt_version=prompt_version,
            style=run_options.style,
            honorific_policy=run_options.honorific_policy,
            preserve_names=run_options.preserve_names,
            selected_glossary_hash=selected_glossary_hash,
        )
        cached = cache_service.get_cached_translation(cache_key=cache_key)
        if cached is not None:
            cache_hit = True
            chunk_repository.update_status(
                job_id=job.id,
                page_id=page.id,
                chunk_index=chunk.chunk_index,
                status="completed",
                translated_text=cached.translated_text,
                elapsed_ms=0,
                clear_error_message=True,
            )
        else:
            messages = self._build_messages(
                run_options=run_options,
                system_prompt=system_prompt,
                source_text=chunk.source_text,
                context_before=chunk.context_before or "",
                context_after=chunk.context_after or "",
                selected_glossary_terms=selected_glossary_terms,
            )
            try:
                result = await self.ollama_client.chat(
                    messages,
                    options=run_options.options,
                    think=run_options.think,
                )
                translated_text = self._extract_translation_text(result.content)
                if not translated_text:
                    raise OllamaClientError(
                        EMPTY_MODEL_RESPONSE_MESSAGE,
                        code="empty_response",
                    )
                chunk_repository.update_status(
                    job_id=job.id,
                    page_id=page.id,
                    chunk_index=chunk.chunk_index,
                    status="completed",
                    translated_text=translated_text,
                    raw_model_response=self._serialize_raw_response(result.raw_response),
                    elapsed_ms=result.elapsed_ms,
                    clear_error_message=True,
                )
                cache_service.save_translation(
                    cache_key=cache_key,
                    source_text=chunk.source_text,
                    translated_text=translated_text,
                    model_name=job.model_name,
                    prompt_version=prompt_version,
                    style=run_options.style,
                    honorific_policy=run_options.honorific_policy,
                    preserve_names=run_options.preserve_names,
                    selected_glossary_hash=selected_glossary_hash,
                )
            except Exception as exc:  # noqa: BLE001
                message = self._map_model_error(exc)
                failed_messages.append(message)
                chunk_repository.update_status(
                    job_id=job.id,
                    page_id=page.id,
                    chunk_index=chunk.chunk_index,
                    status="failed",
                    error_message=message,
                )

        elapsed_ms = self._elapsed_ms(started_at)
        updated_page = self._recalculate_page(
            page,
            page_repository=page_repository,
            chunk_repository=chunk_repository,
            elapsed_ms=elapsed_ms,
        )
        all_pages = page_repository.list_pages(job_id=job.id)
        completed_count = sum(item.completed_chunks for item in all_pages)
        failed_count = sum(item.failed_chunks for item in all_pages)
        total_chunks = sum(item.total_chunks for item in all_pages)
        job_translated_text = "\n\n".join(
            item.translated_text
            for item in all_pages
            if item.translated_text is not None and item.status == "completed"
        )
        translation_repository.update_job(
            job.id,
            translated_text=job_translated_text,
            status=self._job_status(
                completed_count=completed_count,
                failed_count=failed_count,
                total_pages=len(all_pages),
                completed_pages=sum(1 for item in all_pages if item.status == "completed"),
            ),
            total_chunks=total_chunks,
            completed_chunks=completed_count,
            failed_chunks=failed_count,
            elapsed_ms=elapsed_ms,
            error_message=failed_messages[0] if failed_messages else None,
            clear_error_message=not failed_messages,
        )
        page_chunks = chunk_repository.list_chunks(job_id=job.id, page_id=updated_page.id)
        return TranslationResponse(
            job_id=job.id,
            source_type="pasted_text" if job.source_site == "manual" else job.source_site,
            source_lang=run_options.source_lang,
            target_lang=run_options.target_lang,
            current_page_index=updated_page.page_index,
            total_pages=len(all_pages),
            has_next_page=updated_page.page_index < len(all_pages) - 1,
            translated_text=updated_page.translated_text or "",
            model=job.model_name,
            prompt_version=prompt_version,
            style=run_options.style,
            elapsed_ms=elapsed_ms,
            cache_hit=cache_hit,
            chunks=self._chunk_responses_from_db(page_chunks, run_options=run_options),
        )

    async def _translate_job(
        self,
        *,
        job: TranslationJob,
        run_options: TranslationRunOptions,
    ) -> TranslationResponse:
        started_at = time.perf_counter()
        prompt_version = self.prompt_loader.select_prompt_version(
            source_lang=run_options.source_lang,
            target_lang=run_options.target_lang,
            prompt_version=self.prompt_version,
        )
        system_prompt = self.prompt_loader.load(
            prompt_version,
            source_lang=run_options.source_lang,
            target_lang=run_options.target_lang,
        )

        translation_repository = TranslationRepository(self.db)
        chunk_repository = ChunkRepository(self.db)
        page_repository = PageRepository(self.db)
        cache_service = TranslationCacheService(self.db)
        active_glossary_terms = []
        if run_options.use_glossary:
            from app.db.repositories.glossary_repository import GlossaryRepository

            active_glossary_terms = GlossaryRepository(self.db).list_active_terms(
                source_lang=run_options.source_lang,
                target_lang=run_options.target_lang,
            )
        translation_repository.update_job(job.id, status="running")

        pages = page_repository.ensure_pages_for_job(job)
        selected_pages = self._select_pages(
            pages,
            translate_scope=run_options.translate_scope,
            page_index=run_options.page_index,
        )
        translated_pages: dict[int, str] = {}
        selected_chunk_responses: list[TranslationChunkResponse] = []
        failed_messages: list[str] = []
        cache_hit = False

        for page in selected_pages:
            if (
                not run_options.force
                and page.status == "completed"
                and page.translated_text is not None
            ):
                translated_pages[page.page_index] = page.translated_text
                selected_chunk_responses.extend(
                    self._chunk_responses_from_db(
                        chunk_repository.list_chunks(job_id=job.id, page_id=page.id),
                        run_options=run_options,
                    )
                )
                continue

            page_result = await self._translate_page(
                job=job,
                page=page,
                run_options=run_options,
                prompt_version=prompt_version,
                system_prompt=system_prompt,
                active_glossary_terms=active_glossary_terms,
                chunk_repository=chunk_repository,
                page_repository=page_repository,
                cache_service=cache_service,
            )
            translated_pages[page.page_index] = page_result["translated_text"]
            selected_chunk_responses.extend(page_result["chunk_responses"])
            failed_messages.extend(page_result["failed_messages"])
            cache_hit = cache_hit or page_result["cache_hit"]

        translated_text = "\n\n".join(translated_pages[index] for index in sorted(translated_pages))
        all_pages = page_repository.list_pages(job_id=job.id)
        completed_count = sum(page.completed_chunks for page in all_pages)
        failed_count = sum(page.failed_chunks for page in all_pages)
        total_chunks = sum(page.total_chunks for page in all_pages)
        elapsed_ms = self._elapsed_ms(started_at)
        job_translated_text = "\n\n".join(
            page.translated_text
            for page in all_pages
            if page.translated_text is not None and page.status == "completed"
        )
        status = self._job_status(
            completed_count=completed_count,
            failed_count=failed_count,
            total_pages=len(all_pages),
            completed_pages=sum(1 for page in all_pages if page.status == "completed"),
        )
        translation_repository.update_job(
            job.id,
            translated_text=job_translated_text or translated_text,
            status=status,
            total_chunks=total_chunks,
            completed_chunks=completed_count,
            failed_chunks=failed_count,
            elapsed_ms=elapsed_ms,
            error_message=failed_messages[0] if failed_messages else None,
            clear_error_message=not failed_messages,
        )
        current_page_index = selected_pages[0].page_index if selected_pages else 0

        return TranslationResponse(
            job_id=job.id,
            source_type="pasted_text" if job.source_site == "manual" else job.source_site,
            source_lang=run_options.source_lang,
            target_lang=run_options.target_lang,
            current_page_index=current_page_index,
            total_pages=len(all_pages),
            has_next_page=current_page_index < len(all_pages) - 1,
            translated_text=translated_text,
            model=self.model_name,
            prompt_version=prompt_version,
            style=run_options.style,
            elapsed_ms=elapsed_ms,
            cache_hit=cache_hit,
            chunks=sorted(selected_chunk_responses, key=lambda item: item.index),
        )

    async def _translate_page(
        self,
        *,
        job: TranslationJob,
        page: TranslationPage,
        run_options: TranslationRunOptions,
        prompt_version: str,
        system_prompt: str,
        active_glossary_terms: list[Any],
        chunk_repository: ChunkRepository,
        page_repository: PageRepository,
        cache_service: TranslationCacheService,
    ) -> dict[str, Any]:
        page_started_at = time.perf_counter()
        chunks = chunk_text(
            page.source_text,
            max_chars_per_chunk=self.max_chars_per_chunk,
            overlap_paragraphs=self.chunk_overlap_paragraphs,
        )
        page_repository.update_page(page.id, status="running", total_chunks=len(chunks))

        translated_chunks: list[tuple[int, str]] = []
        chunk_responses: list[TranslationChunkResponse] = []
        failed_messages: list[str] = []
        cache_hit = False

        for chunk in chunks:
            chunk_repository.create_chunk(
                job_id=job.id,
                page_id=page.id,
                chunk_index=chunk["index"],
                source_text=chunk["source_text"],
                context_before=chunk["context_before"],
                context_after=chunk["context_after"],
                status="pending",
            )
            chunk_repository.update_status(
                job_id=job.id,
                page_id=page.id,
                chunk_index=chunk["index"],
                status="running",
            )

            selected_glossary_terms = select_glossary_terms_for_text(
                chunk["source_text"],
                active_glossary_terms,
                source_lang=run_options.source_lang,
                target_lang=run_options.target_lang,
            )
            selected_glossary_hash = make_selected_glossary_hash(selected_glossary_terms)
            cache_key = build_cache_key(
                source_text=chunk["source_text"],
                source_lang=run_options.source_lang,
                target_lang=run_options.target_lang,
                model_name=self.model_name,
                prompt_version=prompt_version,
                style=run_options.style,
                honorific_policy=run_options.honorific_policy,
                preserve_names=run_options.preserve_names,
                selected_glossary_hash=selected_glossary_hash,
            )
            if run_options.use_cache:
                cached = cache_service.get_cached_translation(cache_key=cache_key)
                if cached is not None:
                    cache_hit = True
                    translated_text = cached.translated_text
                    chunk_repository.update_status(
                        job_id=job.id,
                        page_id=page.id,
                        chunk_index=chunk["index"],
                        status="completed",
                        translated_text=translated_text,
                        elapsed_ms=0,
                    )
                    translated_chunks.append((chunk["index"], translated_text))
                    chunk_responses.append(
                        TranslationChunkResponse(
                            index=chunk["index"],
                            source_lang=run_options.source_lang,
                            target_lang=run_options.target_lang,
                            status="completed",
                        )
                    )
                    continue

            messages = self._build_messages(
                run_options=run_options,
                system_prompt=system_prompt,
                source_text=chunk["source_text"],
                context_before=chunk["context_before"],
                context_after=chunk["context_after"],
                selected_glossary_terms=selected_glossary_terms,
            )
            try:
                result = await self.ollama_client.chat(
                    messages,
                    options=run_options.options,
                    think=run_options.think,
                )
                translated_text = self._extract_translation_text(result.content)
                if not translated_text:
                    raise OllamaClientError(
                        EMPTY_MODEL_RESPONSE_MESSAGE,
                        code="empty_response",
                    )
                chunk_repository.update_status(
                    job_id=job.id,
                    page_id=page.id,
                    chunk_index=chunk["index"],
                    status="completed",
                    translated_text=translated_text,
                    raw_model_response=self._serialize_raw_response(result.raw_response),
                    elapsed_ms=result.elapsed_ms,
                )
                if run_options.use_cache:
                    cache_service.save_translation(
                        cache_key=cache_key,
                        source_text=chunk["source_text"],
                        translated_text=translated_text,
                        model_name=self.model_name,
                        prompt_version=prompt_version,
                        style=run_options.style,
                        honorific_policy=run_options.honorific_policy,
                        preserve_names=run_options.preserve_names,
                        selected_glossary_hash=selected_glossary_hash,
                    )
                translated_chunks.append((chunk["index"], translated_text))
                chunk_responses.append(
                    TranslationChunkResponse(
                        index=chunk["index"],
                        source_lang=run_options.source_lang,
                        target_lang=run_options.target_lang,
                        status="completed",
                    )
                )
            except Exception as exc:  # noqa: BLE001
                message = self._map_model_error(exc)
                failed_messages.append(message)
                chunk_repository.update_status(
                    job_id=job.id,
                    page_id=page.id,
                    chunk_index=chunk["index"],
                    status="failed",
                    error_message=message,
                    increment_retry_count=True,
                )
                chunk_responses.append(
                    TranslationChunkResponse(
                        index=chunk["index"],
                        source_lang=run_options.source_lang,
                        target_lang=run_options.target_lang,
                        status="failed",
                    )
                )

        translated_text = self._merge_translated_chunks(translated_chunks)
        completed_count = len(translated_chunks)
        failed_count = len(failed_messages)
        page_repository.update_page(
            page.id,
            translated_text=translated_text,
            status=self._page_status(
                completed_count=completed_count,
                failed_count=failed_count,
            ),
            completed_chunks=completed_count,
            failed_chunks=failed_count,
            elapsed_ms=self._elapsed_ms(page_started_at),
            error_message=failed_messages[0] if failed_messages else None,
            clear_error_message=not failed_messages,
        )
        return {
            "translated_text": translated_text,
            "chunk_responses": chunk_responses,
            "failed_messages": failed_messages,
            "cache_hit": cache_hit,
        }

    def _select_pages(
        self,
        pages: list[TranslationPage],
        *,
        translate_scope: str,
        page_index: int,
    ) -> list[TranslationPage]:
        if translate_scope == "first_page":
            page_index = 0
        elif translate_scope == "all_pages":
            return pages
        elif translate_scope != "current_page":
            raise TranslationServiceError("Unsupported translate_scope.", status_code=400)

        for page in pages:
            if page.page_index == page_index:
                return [page]
        raise TranslationServiceError(JOB_NOT_FOUND_MESSAGE, status_code=404)

    def _chunk_responses_from_db(
        self,
        chunks: list[Any],
        *,
        run_options: TranslationRunOptions,
    ) -> list[TranslationChunkResponse]:
        return [
            TranslationChunkResponse(
                index=chunk.chunk_index,
                source_lang=run_options.source_lang,
                target_lang=run_options.target_lang,
                status=chunk.status,
            )
            for chunk in chunks
        ]

    def _run_options_from_job(
        self,
        job: TranslationJob,
        *,
        page_index: int,
    ) -> TranslationRunOptions:
        return TranslationRunOptions(
            source_lang=job.source_language,
            target_lang=job.target_language,
            style=job.style,
            honorific_policy=job.honorific_policy,
            preserve_names=bool(job.preserve_names),
            use_glossary=True,
            use_cache=True,
            think=self._deserialize_ollama_think(job.ollama_think),
            options=self._deserialize_ollama_options(job.ollama_options_json),
            stream=False,
            translate_scope="current_page",
            page_index=page_index,
            force=True,
        )

    def _recalculate_page(
        self,
        page: TranslationPage,
        *,
        page_repository: PageRepository,
        chunk_repository: ChunkRepository,
        elapsed_ms: int,
    ) -> TranslationPage:
        chunks = chunk_repository.list_chunks(job_id=page.job_id, page_id=page.id)
        translated_chunks = [
            (chunk.chunk_index, chunk.translated_text)
            for chunk in chunks
            if chunk.status == "completed" and chunk.translated_text is not None
        ]
        failed_messages = [
            chunk.error_message
            for chunk in chunks
            if chunk.status == "failed" and chunk.error_message
        ]
        completed_count = len(translated_chunks)
        failed_count = sum(1 for chunk in chunks if chunk.status == "failed")
        updated = page_repository.update_page(
            page.id,
            translated_text=self._merge_translated_chunks(translated_chunks),
            status=self._page_status(
                completed_count=completed_count,
                failed_count=failed_count,
            ),
            total_chunks=len(chunks),
            completed_chunks=completed_count,
            failed_chunks=failed_count,
            elapsed_ms=elapsed_ms,
            error_message=failed_messages[0] if failed_messages else None,
            clear_error_message=not failed_messages,
        )
        if updated is None:
            raise TranslationServiceError(JOB_NOT_FOUND_MESSAGE, status_code=404)
        return updated

    def _deserialize_ollama_think(self, value: str | None) -> str | bool:
        if value is None:
            return False
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return value
        if isinstance(parsed, str | bool):
            return parsed
        return False

    def _deserialize_ollama_options(self, value: str | None) -> dict[str, Any] | None:
        if value is None:
            return None
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            return parsed
        return None

    def _validate_request(self, request: TranslationRequest) -> None:
        run_options = TranslationRunOptions(
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            style=request.style,
            honorific_policy=request.honorific_policy,
            preserve_names=request.preserve_names,
            use_glossary=request.use_glossary,
            use_cache=request.use_cache,
            think=request.think,
            options=request.options,
            stream=request.stream,
            translate_scope=request.translate_scope,
            page_index=request.page_index,
        )
        self._validate_run_options(run_options, text=request.text)

    def _validate_run_options(self, run_options: TranslationRunOptions, *, text: str) -> None:
        if not text.strip():
            raise TranslationServiceError(EMPTY_TEXT_MESSAGE, status_code=400)
        if run_options.target_lang != "ko":
            raise TranslationServiceError(ONLY_KO_TARGET_MESSAGE, status_code=400)
        if run_options.stream:
            raise TranslationServiceError(STREAM_NOT_SUPPORTED_MESSAGE, status_code=400)
        if run_options.page_index < 0:
            raise TranslationServiceError(
                "page_index must be greater than or equal to 0.", status_code=400
            )

    def _build_messages(
        self,
        *,
        run_options: TranslationRunOptions,
        system_prompt: str,
        source_text: str,
        context_before: str,
        context_after: str,
        selected_glossary_terms: list[SelectedGlossaryTerm],
    ) -> list[dict[str, str]]:
        glossary_context = self._build_glossary_context(
            enabled=run_options.use_glossary,
            selected_glossary_terms=selected_glossary_terms,
        )
        user_prompt = "\n".join(
            [
                f"source_lang: {run_options.source_lang}",
                f"target_lang: {run_options.target_lang}",
                f"style: {run_options.style}",
                f"honorific_policy: {run_options.honorific_policy}",
                f"preserve_names: {run_options.preserve_names}",
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

    def _build_glossary_context(
        self,
        *,
        enabled: bool,
        selected_glossary_terms: list[SelectedGlossaryTerm],
    ) -> str:
        if not enabled or not selected_glossary_terms:
            return ""
        return build_glossary_context(selected_glossary_terms)

    def _extract_translation_text(self, raw_text: str) -> str:
        text = raw_text.strip()
        for prefix in ("번역문:", "번역:", "Translation:", "Translated text:"):
            if text.startswith(prefix):
                return text[len(prefix) :].strip()
        return text

    def _merge_translated_chunks(self, translated_chunks: list[tuple[int, str]]) -> str:
        return "\n\n".join(text for _, text in sorted(translated_chunks))

    def _page_status(self, *, completed_count: int, failed_count: int) -> str:
        if failed_count == 0:
            return "completed"
        if completed_count == 0:
            return "failed"
        return "partial_failed"

    def _job_status(
        self,
        *,
        completed_count: int,
        failed_count: int,
        total_pages: int,
        completed_pages: int,
    ) -> str:
        if failed_count > 0 and completed_count == 0:
            return "failed"
        if failed_count > 0:
            return "partial_failed"
        if completed_pages == total_pages:
            return "completed"
        return "pending_translation"

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
