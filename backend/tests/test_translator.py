from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import TranslationJob
from app.db.repositories.chunk_repository import ChunkRepository
from app.llm.ollama_client import OllamaClientError
from app.llm.translator import (
    EMPTY_TEXT_MESSAGE,
    ONLY_KO_TARGET_MESSAGE,
    TranslationService,
    TranslationServiceError,
)
from app.schemas.translation import TranslationRequest


SOURCE_TEXT = "\u5f7c\u306f\u9759\u304b\u306b\u76ee\u3092\u9589\u3058\u305f\u3002"


def test_translate_short_text_saves_job_and_chunk(db_session: Session) -> None:
    async def run_test() -> None:
        service = TranslationService(db_session, ollama_client=FakeOllamaClient(["translated"]))

        response = await service.translate_text(TranslationRequest(text=SOURCE_TEXT))

        job = db_session.get(TranslationJob, response.job_id)
        chunks = ChunkRepository(db_session).list_chunks(job_id=response.job_id)

        assert response.source_type == "pasted_text"
        assert response.translated_text == "translated"
        assert response.cache_hit is False
        assert response.chunks[0].status == "completed"
        assert job is not None
        assert job.source_site == "manual"
        assert job.source_url is None
        assert job.original_text == SOURCE_TEXT
        assert job.translated_text == "translated"
        assert job.status == "completed"
        assert job.total_chunks == 1
        assert job.completed_chunks == 1
        assert chunks[0].status == "completed"
        assert chunks[0].translated_text == "translated"

    asyncio.run(run_test())


def test_translate_long_text_uses_multiple_chunks(db_session: Session) -> None:
    async def run_test() -> None:
        service = TranslationService(
            db_session,
            ollama_client=FakeOllamaClient(["first", "second"]),
            max_chars_per_chunk=20,
        )
        text = "\u3042" * 25 + "\n\n" + "\u3044" * 10

        response = await service.translate_text(TranslationRequest(text=text))
        chunks = ChunkRepository(db_session).list_chunks(job_id=response.job_id)

        assert response.translated_text == "first\n\nsecond"
        assert len(response.chunks) == 2
        assert len(chunks) == 2
        assert all(chunk.status == "completed" for chunk in chunks)

    asyncio.run(run_test())


def test_translate_marks_chunk_failure_as_partial_failed(db_session: Session) -> None:
    async def run_test() -> None:
        service = TranslationService(
            db_session,
            ollama_client=FakeOllamaClient(
                ["first"],
                fail_after=1,
                error=OllamaClientError("chunk failed", code="ollama_error"),
            ),
            max_chars_per_chunk=10,
        )

        response = await service.translate_text(TranslationRequest(text="\u3042" * 15))
        job = db_session.get(TranslationJob, response.job_id)
        chunks = ChunkRepository(db_session).list_chunks(job_id=response.job_id)

        assert response.translated_text == "first"
        assert response.chunks[0].status == "completed"
        assert response.chunks[1].status == "failed"
        assert job is not None
        assert job.status == "partial_failed"
        assert job.completed_chunks == 1
        assert job.failed_chunks == 1
        assert chunks[1].status == "failed"
        assert chunks[1].error_message == "chunk failed"

    asyncio.run(run_test())


def test_translate_marks_job_failed_when_all_chunks_fail(db_session: Session) -> None:
    async def run_test() -> None:
        service = TranslationService(
            db_session,
            ollama_client=FakeOllamaClient(
                [],
                fail_after=0,
                error=OllamaClientError("engine down", code="ollama_error"),
            ),
            max_chars_per_chunk=10,
        )

        response = await service.translate_text(TranslationRequest(text="\u3042" * 5))
        job = db_session.get(TranslationJob, response.job_id)

        assert response.translated_text == ""
        assert response.chunks[0].status == "failed"
        assert job is not None
        assert job.status == "failed"
        assert job.completed_chunks == 0
        assert job.failed_chunks == 1
        assert job.error_message == "engine down"

    asyncio.run(run_test())


def test_translate_rejects_empty_text(db_session: Session) -> None:
    async def run_test() -> None:
        service = TranslationService(db_session, ollama_client=FakeOllamaClient(["unused"]))

        try:
            await service.translate_text(TranslationRequest(text="  \n "))
        except TranslationServiceError as exc:
            assert exc.status_code == 400
            assert exc.message == EMPTY_TEXT_MESSAGE
            return

        raise AssertionError("TranslationServiceError was not raised")

    asyncio.run(run_test())


def test_translate_rejects_non_ko_target(db_session: Session) -> None:
    async def run_test() -> None:
        service = TranslationService(db_session, ollama_client=FakeOllamaClient(["unused"]))

        try:
            await service.translate_text(TranslationRequest(text=SOURCE_TEXT, target_lang="en"))
        except TranslationServiceError as exc:
            assert exc.status_code == 400
            assert exc.message == ONLY_KO_TARGET_MESSAGE
            return

        raise AssertionError("TranslationServiceError was not raised")

    asyncio.run(run_test())


class FakeOllamaClient:
    def __init__(
        self,
        responses: list[str],
        *,
        fail_after: int | None = None,
        error: Exception | None = None,
    ) -> None:
        self.responses = responses
        self.fail_after = fail_after
        self.error = error or RuntimeError("failed")
        self.calls: list[dict[str, Any]] = []

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        options: dict[str, Any] | None = None,
        think: str | bool | None = None,
    ) -> SimpleNamespace:
        self.calls.append({"messages": messages, "options": options, "think": think})
        call_index = len(self.calls) - 1
        if self.fail_after is not None and call_index >= self.fail_after:
            raise self.error

        content = self.responses[call_index]
        return SimpleNamespace(
            content=content,
            text=content,
            model="gemma4:26b-a4b-it-q4_K_M",
            elapsed_ms=12,
            raw_response={"message": {"content": content}},
        )
