from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import TranslationCache
from app.llm.translator import TranslationService
from app.schemas.translation import TranslationRequest
from app.services.cache import build_cache_key

BASE_KEY_ARGS = {
    "source_text": "Sword of Dawn",
    "source_lang": "en",
    "target_lang": "ko",
    "model_name": "gemma4:26b-a4b-it-q4_K_M",
    "prompt_version": "translate_en_ko_v1",
    "style": "webnovel",
    "honorific_policy": "preserve",
    "preserve_names": True,
    "selected_glossary_hash": "selected-glossary-a",
}


def test_source_lang_change_makes_cache_miss() -> None:
    assert build_cache_key(**BASE_KEY_ARGS) != build_cache_key(
        **{
            **BASE_KEY_ARGS,
            "source_lang": "zh-CN",
            "prompt_version": "translate_zh_ko_v1",
        }
    )


def test_translator_cache_rows_store_language_pair(db_session: Session) -> None:
    async def run_test() -> None:
        fake_client = FakeOllamaClient(["영어 번역", "일본어 설정 번역"])
        service = TranslationService(db_session, ollama_client=fake_client)

        first = await service.translate_text(
            TranslationRequest(text="Sword of Dawn", source_lang="en")
        )
        second = await service.translate_text(
            TranslationRequest(text="Sword of Dawn", source_lang="ja")
        )
        cache_entries = db_session.query(TranslationCache).order_by(TranslationCache.id).all()

        assert first.cache_hit is False
        assert second.cache_hit is False
        assert len(fake_client.calls) == 2
        assert [(entry.source_lang, entry.target_lang) for entry in cache_entries] == [
            ("en", "ko"),
            ("ja", "ko"),
        ]

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
