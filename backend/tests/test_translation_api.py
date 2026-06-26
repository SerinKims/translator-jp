from __future__ import annotations

from collections.abc import Generator
from types import SimpleNamespace
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.translate import get_translation_service
from app.db.models import TranslationJob
from app.db.session import get_db
from app.llm.ollama_client import OllamaClientError
from app.llm.translator import (
    MODEL_NOT_FOUND_MESSAGE,
    ONLY_KO_TARGET_MESSAGE,
    TranslationService,
)
from app.main import app


SOURCE_TEXT = "\u5f7c\u306f\u9759\u304b\u306b\u76ee\u3092\u9589\u3058\u305f\u3002"


def test_translate_api_returns_translation_response(db_session: Session) -> None:
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_translation_service] = lambda: TranslationService(
        db_session,
        ollama_client=FakeOllamaClient(["translated"]),
    )

    try:
        client = TestClient(app)
        response = client.post("/api/translate", json={"text": SOURCE_TEXT})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"] == 1
    assert payload["source_type"] == "pasted_text"
    assert payload["source_lang"] == "ja"
    assert payload["target_lang"] == "ko"
    assert payload["current_page_index"] == 0
    assert payload["total_pages"] == 1
    assert payload["has_next_page"] is False
    assert payload["translated_text"] == "translated"
    assert payload["model"] == "gemma4:26b-a4b-it-q4_K_M"
    assert payload["prompt_version"] == "translate_ja_ko_v1"
    assert payload["style"] == "webnovel"
    assert payload["cache_hit"] is False
    assert payload["chunks"] == [
        {
            "index": 0,
            "source_lang": "ja",
            "target_lang": "ko",
            "status": "completed",
        }
    ]

    saved = db_session.get(TranslationJob, 1)
    assert saved is not None
    assert saved.status == "completed"
    assert saved.source_site == "manual"


def test_translate_api_second_same_request_returns_cache_hit(db_session: Session) -> None:
    fake_client = FakeOllamaClient(["translated"])
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_translation_service] = lambda: TranslationService(
        db_session,
        ollama_client=fake_client,
    )

    try:
        client = TestClient(app)
        first = client.post("/api/translate", json={"text": SOURCE_TEXT})
        second = client.post("/api/translate", json={"text": SOURCE_TEXT})
    finally:
        app.dependency_overrides.clear()

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["cache_hit"] is False
    assert second.json()["cache_hit"] is True
    assert second.json()["translated_text"] == "translated"
    assert len(fake_client.calls) == 1


def test_translate_api_use_cache_false_bypasses_existing_cache(db_session: Session) -> None:
    fake_client = FakeOllamaClient(["cached translation", "fresh translation"])
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_translation_service] = lambda: TranslationService(
        db_session,
        ollama_client=fake_client,
    )

    try:
        client = TestClient(app)
        first = client.post("/api/translate", json={"text": SOURCE_TEXT})
        second = client.post(
            "/api/translate",
            json={"text": SOURCE_TEXT, "use_cache": False},
        )
    finally:
        app.dependency_overrides.clear()

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["cache_hit"] is False
    assert second.json()["cache_hit"] is False
    assert second.json()["translated_text"] == "fresh translation"
    assert len(fake_client.calls) == 2


def test_translate_api_rejects_non_ko_target(db_session: Session) -> None:
    app.dependency_overrides[get_translation_service] = lambda: TranslationService(
        db_session,
        ollama_client=FakeOllamaClient(["unused"]),
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/api/translate",
            json={"text": SOURCE_TEXT, "target_lang": "en"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == ONLY_KO_TARGET_MESSAGE


def test_translate_api_maps_ollama_model_not_found(db_session: Session) -> None:
    app.dependency_overrides[get_translation_service] = lambda: TranslationService(
        db_session,
        ollama_client=FakeOllamaClient(
            [],
            error=OllamaClientError("missing", code="model_not_found"),
        ),
    )

    try:
        client = TestClient(app)
        response = client.post("/api/translate", json={"text": SOURCE_TEXT})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    saved = db_session.get(TranslationJob, 1)
    assert saved is not None
    assert saved.status == "failed"
    assert saved.error_message == MODEL_NOT_FOUND_MESSAGE
    assert response.json()["chunks"][0]["status"] == "failed"


def _override_db(db_session: Session):
    def _get_db() -> Generator[Session, None, None]:
        yield db_session

    return _get_db


class FakeOllamaClient:
    def __init__(self, responses: list[str], *, error: Exception | None = None) -> None:
        self.responses = responses
        self.error = error
        self.calls: list[dict[str, Any]] = []

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        options: dict[str, Any] | None = None,
        think: str | bool | None = None,
    ) -> SimpleNamespace:
        self.calls.append({"messages": messages, "options": options, "think": think})
        if self.error is not None:
            raise self.error

        content = self.responses[len(self.calls) - 1]
        return SimpleNamespace(
            content=content,
            text=content,
            model="gemma4:26b-a4b-it-q4_K_M",
            elapsed_ms=10,
            raw_response={"message": {"content": content}},
        )
