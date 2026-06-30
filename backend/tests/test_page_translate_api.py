from __future__ import annotations

from collections.abc import Generator
from types import SimpleNamespace
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.translate import get_translation_service
from app.db.models import TranslationChunk
from app.db.repositories.page_repository import PageRepository
from app.db.session import get_db
from app.llm.translator import TranslationService
from app.main import app

PAGE_TEXT = "一ページ目[newpage]二ページ目[newpage]三ページ目"


def test_translate_defaults_to_first_page_only(db_session: Session) -> None:
    fake_client = FakeOllamaClient(["첫 페이지"])
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_translation_service] = lambda: TranslationService(
        db_session,
        ollama_client=fake_client,
    )

    try:
        client = TestClient(app)
        response = client.post("/api/translate", json={"text": PAGE_TEXT})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["current_page_index"] == 0
    assert payload["total_pages"] == 3
    assert payload["has_next_page"] is True
    assert payload["translated_text"] == "첫 페이지"
    assert len(fake_client.calls) == 1

    pages = PageRepository(db_session).list_pages(job_id=payload["job_id"])
    assert [page.status for page in pages] == ["completed", "pending", "pending"]
    chunks = db_session.query(TranslationChunk).all()
    assert len(chunks) == 1
    assert chunks[0].page_id == pages[0].id


def test_translate_next_page_translates_only_requested_page(db_session: Session) -> None:
    fake_client = FakeOllamaClient(["첫 페이지", "둘째 페이지"])
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_translation_service] = lambda: TranslationService(
        db_session,
        ollama_client=fake_client,
    )

    try:
        client = TestClient(app)
        first = client.post("/api/translate", json={"text": PAGE_TEXT})
        second = client.post(
            f"/api/translations/{first.json()['job_id']}/pages/1/translate",
            json={},
        )
    finally:
        app.dependency_overrides.clear()

    assert first.status_code == 200
    assert second.status_code == 200
    payload = second.json()
    assert payload["current_page_index"] == 1
    assert payload["total_pages"] == 3
    assert payload["has_next_page"] is True
    assert payload["translated_text"] == "둘째 페이지"
    assert len(fake_client.calls) == 2

    pages = PageRepository(db_session).list_pages(job_id=payload["job_id"])
    assert [page.status for page in pages] == ["completed", "completed", "pending"]
    chunks = db_session.query(TranslationChunk).order_by(TranslationChunk.id).all()
    assert [chunk.page_id for chunk in chunks] == [pages[0].id, pages[1].id]


def test_translate_reuses_completed_page_from_database(db_session: Session) -> None:
    fake_client = FakeOllamaClient(["첫 페이지"])
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_translation_service] = lambda: TranslationService(
        db_session,
        ollama_client=fake_client,
    )

    try:
        client = TestClient(app)
        first = client.post("/api/translate", json={"text": PAGE_TEXT})
        reused = client.post(
            f"/api/translations/{first.json()['job_id']}/pages/0/translate",
            json={},
        )
    finally:
        app.dependency_overrides.clear()

    assert reused.status_code == 200
    assert reused.json()["translated_text"] == "첫 페이지"
    assert len(fake_client.calls) == 1


def test_translate_all_pages_requires_explicit_scope(db_session: Session) -> None:
    fake_client = FakeOllamaClient(["첫 페이지", "둘째 페이지", "셋째 페이지"])
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_translation_service] = lambda: TranslationService(
        db_session,
        ollama_client=fake_client,
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/api/translate",
            json={"text": PAGE_TEXT, "translate_scope": "all_pages"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["current_page_index"] == 0
    assert payload["total_pages"] == 3
    assert payload["has_next_page"] is True
    assert payload["translated_text"] == "첫 페이지\n\n둘째 페이지\n\n셋째 페이지"
    assert len(fake_client.calls) == 3

    pages = PageRepository(db_session).list_pages(job_id=payload["job_id"])
    assert [page.status for page in pages] == ["completed", "completed", "completed"]
    chunks = db_session.query(TranslationChunk).order_by(TranslationChunk.id).all()
    assert [chunk.page_id for chunk in chunks] == [page.id for page in pages]


def _override_db(db_session: Session):
    def _get_db() -> Generator[Session, None, None]:
        yield db_session

    return _get_db


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
