from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import TranslationJob
from app.db.repositories.cache_repository import CacheRepository
from app.db.repositories.chunk_repository import ChunkRepository
from app.db.repositories.glossary_repository import GlossaryRepository
from app.db.repositories.translation_repository import TranslationRepository
from app.llm.ollama_client import OllamaClientError
from app.llm.translator import (
    EMPTY_TEXT_MESSAGE,
    ONLY_KO_TARGET_MESSAGE,
    TranslationService,
    TranslationServiceError,
)
from app.schemas.translation import TranslationRequest
from app.services.cache import build_cache_key
from app.services.glossary import make_selected_glossary_hash

SOURCE_TEXT = "\u5f7c\u306f\u9759\u304b\u306b\u76ee\u3092\u9589\u3058\u305f\u3002"
ESCAPED_TITLE = "\\u4f5c\\u54c1\\u30bf\\u30a4\\u30c8\\u30eb"
RESTORED_TITLE = "\u4f5c\u54c1\u30bf\u30a4\u30c8\u30eb"


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


def test_translate_restores_literal_unicode_escapes_before_saving(
    db_session: Session,
) -> None:
    async def run_test() -> None:
        service = TranslationService(
            db_session,
            ollama_client=FakeOllamaClient([ESCAPED_TITLE]),
        )

        response = await service.translate_text(TranslationRequest(text=SOURCE_TEXT))

        job = db_session.get(TranslationJob, response.job_id)
        chunks = ChunkRepository(db_session).list_chunks(job_id=response.job_id)

        assert response.translated_text == RESTORED_TITLE
        assert job is not None
        assert job.translated_text == RESTORED_TITLE
        assert chunks[0].translated_text == RESTORED_TITLE
        assert chunks[0].raw_model_response is not None
        assert ESCAPED_TITLE.replace("\\", "\\\\") in chunks[0].raw_model_response

    asyncio.run(run_test())


def test_translate_restores_prefixed_literal_unicode_escapes(
    db_session: Session,
) -> None:
    async def run_test() -> None:
        service = TranslationService(
            db_session,
            ollama_client=FakeOllamaClient([f"Translation: {ESCAPED_TITLE}"]),
        )

        response = await service.translate_text(TranslationRequest(text=SOURCE_TEXT))

        job = db_session.get(TranslationJob, response.job_id)
        chunks = ChunkRepository(db_session).list_chunks(job_id=response.job_id)

        assert response.translated_text == RESTORED_TITLE
        assert job is not None
        assert job.translated_text == RESTORED_TITLE
        assert chunks[0].translated_text == RESTORED_TITLE

    asyncio.run(run_test())


def test_translate_cache_hit_restores_literal_unicode_escapes(
    db_session: Session,
) -> None:
    async def run_test() -> None:
        selected_glossary_hash = make_selected_glossary_hash([])
        cache_key = build_cache_key(
            source_text=SOURCE_TEXT,
            source_lang="ja",
            target_lang="ko",
            model_name="gemma4:26b-a4b-it-q4_K_M",
            prompt_version="translate_ja_ko_v1",
            style="webnovel",
            honorific_policy="preserve",
            preserve_names=True,
            selected_glossary_hash=selected_glossary_hash,
        )
        CacheRepository(db_session).create_cache_entry(
            cache_key=cache_key,
            source_text=SOURCE_TEXT,
            translated_text=ESCAPED_TITLE,
            selected_glossary_hash=selected_glossary_hash,
        )
        fake_client = FakeOllamaClient(["unused"])
        service = TranslationService(db_session, ollama_client=fake_client)

        response = await service.translate_text(TranslationRequest(text=SOURCE_TEXT))

        job = db_session.get(TranslationJob, response.job_id)
        chunks = ChunkRepository(db_session).list_chunks(job_id=response.job_id)

        assert response.cache_hit is True
        assert response.translated_text == RESTORED_TITLE
        assert len(fake_client.calls) == 0
        assert job is not None
        assert job.translated_text == RESTORED_TITLE
        assert chunks[0].translated_text == RESTORED_TITLE

    asyncio.run(run_test())


def test_translate_same_text_second_request_uses_cache(db_session: Session) -> None:
    async def run_test() -> None:
        fake_client = FakeOllamaClient(["translated"])
        service = TranslationService(db_session, ollama_client=fake_client)

        first = await service.translate_text(TranslationRequest(text=SOURCE_TEXT))
        second = await service.translate_text(TranslationRequest(text=SOURCE_TEXT))

        assert first.cache_hit is False
        assert second.cache_hit is True
        assert second.translated_text == "translated"
        assert len(fake_client.calls) == 1

    asyncio.run(run_test())


def test_translate_use_cache_false_bypasses_existing_cache(db_session: Session) -> None:
    async def run_test() -> None:
        fake_client = FakeOllamaClient(["cached translation", "fresh translation"])
        service = TranslationService(db_session, ollama_client=fake_client)

        await service.translate_text(TranslationRequest(text=SOURCE_TEXT))
        response = await service.translate_text(
            TranslationRequest(text=SOURCE_TEXT, use_cache=False)
        )

        assert response.cache_hit is False
        assert response.translated_text == "fresh translation"
        assert len(fake_client.calls) == 2

    asyncio.run(run_test())


def test_translate_style_change_calls_ollama_again(db_session: Session) -> None:
    async def run_test() -> None:
        fake_client = FakeOllamaClient(["webnovel translation", "literal translation"])
        service = TranslationService(db_session, ollama_client=fake_client)

        await service.translate_text(TranslationRequest(text=SOURCE_TEXT, style="webnovel"))
        response = await service.translate_text(
            TranslationRequest(text=SOURCE_TEXT, style="literal")
        )

        assert response.cache_hit is False
        assert response.translated_text == "literal translation"
        assert len(fake_client.calls) == 2

    asyncio.run(run_test())


def test_translate_source_lang_change_calls_ollama_again(db_session: Session) -> None:
    async def run_test() -> None:
        fake_client = FakeOllamaClient(["ja translation", "en translation"])
        service = TranslationService(
            db_session,
            ollama_client=fake_client,
            prompt_loader=FakePromptLoader(),
        )

        await service.translate_text(TranslationRequest(text=SOURCE_TEXT, source_lang="ja"))
        response = await service.translate_text(
            TranslationRequest(text=SOURCE_TEXT, source_lang="en")
        )

        assert response.cache_hit is False
        assert response.translated_text == "en translation"
        assert len(fake_client.calls) == 2

    asyncio.run(run_test())


def test_translate_selected_glossary_change_calls_ollama_again(db_session: Session) -> None:
    async def run_test() -> None:
        fake_client = FakeOllamaClient(["without glossary", "with glossary"])
        service = TranslationService(db_session, ollama_client=fake_client)
        text = "魔王は静かに笑った。"

        await service.translate_text(TranslationRequest(text=text))
        GlossaryRepository(db_session).create_term(
            source_term="魔王",
            target_term="마왕",
            term_type="title",
        )
        response = await service.translate_text(TranslationRequest(text=text))

        assert response.cache_hit is False
        assert response.translated_text == "with glossary"
        assert len(fake_client.calls) == 2

    asyncio.run(run_test())


def test_translate_use_glossary_true_injects_selected_glossary_context(
    db_session: Session,
) -> None:
    async def run_test() -> None:
        fake_client = FakeOllamaClient(["translated"])
        service = TranslationService(db_session, ollama_client=fake_client)
        GlossaryRepository(db_session).create_term(
            source_term="王都",
            target_term="왕도",
            term_type="place",
            aliases=["王城"],
            priority=80,
        )

        await service.translate_text(TranslationRequest(text="王城の門が開いた。"))

        user_prompt = fake_client.calls[0]["messages"][1]["content"]
        assert "[용어집 - 반드시 지킬 것]" in user_prompt
        assert "王都=왕도" in user_prompt

    asyncio.run(run_test())


def test_translate_use_glossary_false_does_not_inject_glossary_context(
    db_session: Session,
) -> None:
    async def run_test() -> None:
        fake_client = FakeOllamaClient(["translated"])
        service = TranslationService(db_session, ollama_client=fake_client)
        GlossaryRepository(db_session).create_term(
            source_term="王都",
            target_term="왕도",
            term_type="place",
        )

        await service.translate_text(
            TranslationRequest(text="王都の門が開いた。", use_glossary=False)
        )

        user_prompt = fake_client.calls[0]["messages"][1]["content"]
        assert "[용어집 - 반드시 지킬 것]" not in user_prompt
        assert "王都=왕도" not in user_prompt

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


def test_translate_existing_pixiv_job_reuses_job_id(db_session: Session) -> None:
    async def run_test() -> None:
        repository = TranslationRepository(db_session)
        job = repository.create_job(
            source_site="pixiv",
            source_url="https://www.pixiv.net/novel/show.php?id=12345678",
            source_title="title",
            source_author="author",
            source_work_id="12345678",
            original_text=SOURCE_TEXT,
            status="fetched",
        )
        service = TranslationService(db_session, ollama_client=FakeOllamaClient(["translated"]))

        response = await service.translate_job(
            job.id,
            source_lang="ja",
            target_lang="ko",
            style="webnovel",
            honorific_policy="preserve",
            preserve_names=True,
            use_glossary=True,
            use_cache=True,
            think=False,
            options=None,
        )

        saved = db_session.get(TranslationJob, job.id)
        chunks = ChunkRepository(db_session).list_chunks(job_id=job.id)

        assert response.job_id == job.id
        assert len(repository.list_jobs()) == 1
        assert saved is not None
        assert saved.source_site == "pixiv"
        assert saved.status == "completed"
        assert saved.translated_text == "translated"
        assert saved.completed_chunks == 1
        assert chunks[0].status == "completed"
        assert chunks[0].translated_text == "translated"

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


class FakePromptLoader:
    def select_prompt_version(
        self,
        *,
        source_lang: str,
        target_lang: str,
        prompt_version: str | None = None,
    ) -> str:
        return prompt_version or "translate_ja_ko_v1"

    def load(
        self,
        prompt_version: str,
        *,
        source_lang: str,
        target_lang: str,
    ) -> str:
        return "system prompt"
