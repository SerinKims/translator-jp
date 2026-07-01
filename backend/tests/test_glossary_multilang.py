from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

from sqlalchemy.orm import Session

from app.db.repositories.glossary_repository import GlossaryRepository
from app.llm.translator import TranslationService
from app.schemas.translation import TranslationRequest
from app.services.glossary import select_glossary_terms_for_text


def test_selects_only_matching_language_glossary_terms() -> None:
    selected = select_glossary_terms_for_text(
        "Sword of Dawn",
        [
            {
                "source_lang": "en",
                "target_lang": "ko",
                "source_term": "Sword",
                "target_term": "검",
            },
            {
                "source_lang": "ja",
                "target_lang": "ko",
                "source_term": "Sword",
                "target_term": "소드",
            },
        ],
        source_lang="en",
        target_lang="ko",
    )

    assert [(term.source_lang, term.target_term) for term in selected] == [("en", "검")]


def test_translator_applies_glossary_for_matching_source_language(
    db_session: Session,
) -> None:
    async def run_test() -> None:
        GlossaryRepository(db_session).create_term(
            source_lang="en",
            target_lang="ko",
            source_term="Sword",
            target_term="검",
        )
        GlossaryRepository(db_session).create_term(
            source_lang="ja",
            target_lang="ko",
            source_term="Sword",
            target_term="소드",
        )
        fake_client = FakeOllamaClient(["새벽의 검"])
        service = TranslationService(db_session, ollama_client=fake_client)

        await service.translate_text(TranslationRequest(text="Sword of Dawn", source_lang="en"))
        user_prompt = fake_client.calls[0]["messages"][1]["content"]

        assert "Sword=검" in user_prompt
        assert "Sword=소드" not in user_prompt

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
