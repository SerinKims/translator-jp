from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import TranslationJob
from app.db.repositories.chunk_repository import ChunkRepository
from app.llm.translator import (
    ONLY_KO_TARGET_MESSAGE,
    UNKNOWN_SOURCE_LANGUAGE_MESSAGE,
    TranslationService,
    TranslationServiceError,
)
from app.schemas.translation import TranslationRequest


def test_auto_detects_japanese_and_keeps_existing_translation_request(
    db_session: Session,
) -> None:
    async def run_test() -> None:
        service = TranslationService(db_session, ollama_client=FakeOllamaClient(["번역"]))

        response = await service.translate_text(
            TranslationRequest(text="彼は静かに目を閉じた。これは夢ではない。", source_lang="auto")
        )
        job = db_session.get(TranslationJob, response.job_id)
        chunks = ChunkRepository(db_session).list_chunks(job_id=response.job_id)

        assert response.source_lang == "ja"
        assert response.prompt_version == "translate_ja_ko_v1"
        assert job is not None
        assert job.source_language == "ja"
        assert job.detected_lang == "ja"
        assert job.language_confidence is not None
        assert chunks[0].source_lang == "ja"
        assert chunks[0].target_lang == "ko"

    asyncio.run(run_test())


def test_direct_english_request_selects_english_prompt(db_session: Session) -> None:
    async def run_test() -> None:
        fake_client = FakeOllamaClient(["그는 눈을 감았다."])
        service = TranslationService(db_session, ollama_client=fake_client)

        response = await service.translate_text(
            TranslationRequest(
                text="He closed his eyes and waited for dawn.",
                source_lang="en",
            )
        )
        job = db_session.get(TranslationJob, response.job_id)
        user_prompt = fake_client.calls[0]["messages"][1]["content"]

        assert response.source_lang == "en"
        assert response.prompt_version == "translate_en_ko_v1"
        assert "영어 소설" in fake_client.calls[0]["messages"][0]["content"]
        assert "source_lang: en" in user_prompt
        assert job is not None
        assert job.source_language == "en"
        assert job.detected_lang == "en"
        assert job.language_confidence == 1.0

    asyncio.run(run_test())


def test_direct_chinese_request_selects_chinese_prompt(db_session: Session) -> None:
    async def run_test() -> None:
        fake_client = FakeOllamaClient(["그는 조용히 눈을 감았다."])
        service = TranslationService(db_session, ollama_client=fake_client)

        response = await service.translate_text(
            TranslationRequest(
                text="他静静地闭上了眼睛。",
                source_lang="zh-CN",
            )
        )

        assert response.source_lang == "zh-CN"
        assert response.prompt_version == "translate_zh_ko_v1"
        assert "중국어 소설" in fake_client.calls[0]["messages"][0]["content"]

    asyncio.run(run_test())


def test_auto_detects_english(db_session: Session) -> None:
    async def run_test() -> None:
        service = TranslationService(db_session, ollama_client=FakeOllamaClient(["번역"]))

        response = await service.translate_text(
            TranslationRequest(
                text="The mage opened the old wooden door.",
                source_lang="auto",
            )
        )

        assert response.source_lang == "en"
        assert response.prompt_version == "translate_en_ko_v1"

    asyncio.run(run_test())


def test_auto_detects_chinese(db_session: Session) -> None:
    async def run_test() -> None:
        service = TranslationService(db_session, ollama_client=FakeOllamaClient(["번역"]))

        response = await service.translate_text(
            TranslationRequest(text="他推开门，风雪涌入屋内。", source_lang="auto")
        )

        assert response.source_lang == "zh-CN"
        assert response.prompt_version == "translate_zh_ko_v1"

    asyncio.run(run_test())


def test_non_ko_target_is_rejected(db_session: Session) -> None:
    async def run_test() -> None:
        service = TranslationService(db_session, ollama_client=FakeOllamaClient(["unused"]))

        try:
            await service.translate_text(
                TranslationRequest(text="He closed his eyes.", source_lang="en", target_lang="en")
            )
        except TranslationServiceError as exc:
            assert exc.status_code == 400
            assert exc.message == ONLY_KO_TARGET_MESSAGE
            return

        raise AssertionError("TranslationServiceError was not raised")

    asyncio.run(run_test())


def test_unknown_auto_language_is_rejected(db_session: Session) -> None:
    async def run_test() -> None:
        service = TranslationService(db_session, ollama_client=FakeOllamaClient(["unused"]))

        try:
            await service.translate_text(TranslationRequest(text="12345 !!!", source_lang="auto"))
        except TranslationServiceError as exc:
            assert exc.status_code == 400
            assert exc.message == UNKNOWN_SOURCE_LANGUAGE_MESSAGE
            return

        raise AssertionError("TranslationServiceError was not raised")

    asyncio.run(run_test())


class FakeOllamaClient:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        options: dict[str, Any] | None = None,
        think: str | bool | None = None,
    ) -> SimpleNamespace:
        self.calls.append({"messages": messages, "options": options, "think": think})
        content = self.responses[len(self.calls) - 1]
        return SimpleNamespace(
            content=content,
            text=content,
            model="gemma4:26b-a4b-it-q4_K_M",
            elapsed_ms=10,
            raw_response={"message": {"content": content}},
        )
