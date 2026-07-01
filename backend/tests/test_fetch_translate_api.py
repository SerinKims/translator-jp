from __future__ import annotations

import json
from collections.abc import Generator
from types import SimpleNamespace
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.fetch import get_fetch_service
from app.crawler.pixiv_types import PixivFetchedPage
from app.crawler.url_validator import INVALID_PIXIV_URL_MESSAGE
from app.db.models import TranslationCache, TranslationJob
from app.db.repositories.glossary_repository import GlossaryRepository
from app.db.repositories.page_repository import PageRepository
from app.db.session import get_db
from app.llm.translator import TranslationService
from app.main import app
from app.schemas.fetch import PixivTranslateResponse
from app.schemas.translation import TranslationChunkResponse
from app.services.fetch_service import FetchService


PIXIV_URL = "https://www.pixiv.net/novel/show.php?id=12345678"
TITLE = "\u4f5c\u54c1\u30bf\u30a4\u30c8\u30eb"
AUTHOR = "\u4f5c\u8005\u540d"
FIRST_PAGE = "\u9b54\u738b\u306f\u7a93\u306e\u5916\u3092\u898b\u305f\u3002"
SECOND_PAGE = "\u52c7\u8005\u306f\u6249\u3092\u958b\u3051\u305f\u3002"
PAGE_TEXT = f"{FIRST_PAGE}[newpage]{SECOND_PAGE}"


class FakePixivClient:
    def __init__(self, text: str = PAGE_TEXT) -> None:
        self.text = text
        self.urls: list[str] = []

    async def fetch_html(self, url: str) -> PixivFetchedPage:
        self.urls.append(url)
        payload = {
            "novel": {
                "12345678": {
                    "title": TITLE,
                    "userName": AUTHOR,
                    "content": self.text,
                }
            }
        }
        html = (
            '<html><head><meta id="meta-preload-data" content=\''
            + json.dumps(payload, ensure_ascii=True)
            + "'></head><body></body></html>"
        )
        return PixivFetchedPage(url=url, html=html, status_code=200)


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
            elapsed_ms=12,
            raw_response={"message": {"content": content}},
        )


class FailingOllamaClient:
    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        options: dict[str, Any] | None = None,
        think: str | bool | None = None,
    ) -> SimpleNamespace:
        raise RuntimeError("model exploded")


class FakeFetchTranslateService:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def fetch_and_translate_pixiv(self, **kwargs: Any) -> PixivTranslateResponse:
        self.calls.append(kwargs)
        return PixivTranslateResponse(
            job_id=7,
            source_site="pixiv",
            source_url=kwargs["url"],
            source_work_id="12345678",
            title=TITLE,
            author=AUTHOR,
            current_page_index=kwargs["page_index"],
            total_pages=3,
            has_next_page=True,
            translated_text="mocked translation",
            model="gemma4:26b-a4b-it-q4_K_M",
            prompt_version="translate_ja_ko_v1",
            elapsed_ms=5,
            chunks=[
                TranslationChunkResponse(
                    index=0,
                    source_lang=kwargs["source_lang"],
                    target_lang=kwargs["target_lang"],
                    status="completed",
                )
            ],
        )


def test_fetch_translate_route_passes_request_to_fetch_service(db_session: Session) -> None:
    fake_service = FakeFetchTranslateService()
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_fetch_service] = lambda: fake_service

    try:
        client = TestClient(app)
        response = client.post(
            "/api/fetch/pixiv/translate",
            json={
                "url": PIXIV_URL,
                "source_lang": "ja",
                "target_lang": "ko",
                "translate_scope": "current_page",
                "page_index": 1,
                "style": "webnovel",
                "honorific_policy": "preserve",
                "preserve_names": True,
                "use_glossary": True,
                "use_cache": True,
                "think": "low",
                "options": {"temperature": 0.2},
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert fake_service.calls == [
        {
            "url": PIXIV_URL,
            "source_lang": "ja",
            "target_lang": "ko",
            "translate_scope": "current_page",
            "page_index": 1,
            "style": "webnovel",
            "honorific_policy": "preserve",
            "preserve_names": True,
            "use_glossary": True,
            "use_cache": True,
            "stream": False,
            "think": "low",
            "options": {"temperature": 0.2},
        }
    ]
    assert response.json()["current_page_index"] == 1


def test_fetch_translate_with_translator_mock_saves_source_metadata(
    db_session: Session,
) -> None:
    fake_ollama = FakeOllamaClient(["translated first page"])
    service = FetchService(
        db_session,
        pixiv_client=FakePixivClient(),
        translation_service=TranslationService(db_session, ollama_client=fake_ollama),
    )
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_fetch_service] = lambda: service

    try:
        client = TestClient(app)
        response = client.post(
            "/api/fetch/pixiv/translate",
            json={
                "url": PIXIV_URL,
                "translate_scope": "first_page",
                "page_index": 0,
                "think": "low",
                "options": {"temperature": 0.2, "max_tokens": 2048},
            },
        )
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    job = db_session.get(TranslationJob, body["job_id"])

    assert response.status_code == 200
    assert body["source_site"] == "pixiv"
    assert body["source_work_id"] == "12345678"
    assert body["title"] == TITLE
    assert body["author"] == AUTHOR
    assert body["translated_text"] == "translated first page"
    assert body["current_page_index"] == 0
    assert body["total_pages"] == 2
    assert body["has_next_page"] is True
    assert job is not None
    assert job.source_site == "pixiv"
    assert job.source_url == PIXIV_URL
    assert job.source_title == TITLE
    assert job.source_author == AUTHOR
    assert job.source_work_id == "12345678"
    assert job.original_text == PAGE_TEXT
    assert job.ollama_think == '"low"'
    assert job.ollama_options_json == '{"max_tokens": 2048, "temperature": 0.2}'


def test_fetch_translate_splits_newpage_and_translates_first_page_only(
    db_session: Session,
) -> None:
    fake_ollama = FakeOllamaClient(["translated first page"])
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_fetch_service] = lambda: FetchService(
        db_session,
        pixiv_client=FakePixivClient(),
        translation_service=TranslationService(db_session, ollama_client=fake_ollama),
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/api/fetch/pixiv/translate",
            json={"url": PIXIV_URL, "translate_scope": "first_page", "page_index": 0},
        )
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    pages = PageRepository(db_session).list_pages(job_id=body["job_id"])

    assert response.status_code == 200
    assert len(fake_ollama.calls) == 1
    assert body["translated_text"] == "translated first page"
    assert [page.source_text for page in pages] == [FIRST_PAGE, SECOND_PAGE]
    assert [page.status for page in pages] == ["completed", "pending"]


def test_fetch_translate_records_failed_chunk_without_running_successfully(
    db_session: Session,
) -> None:
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_fetch_service] = lambda: FetchService(
        db_session,
        pixiv_client=FakePixivClient(text=FIRST_PAGE),
        translation_service=TranslationService(db_session, ollama_client=FailingOllamaClient()),
    )

    try:
        client = TestClient(app)
        response = client.post("/api/fetch/pixiv/translate", json={"url": PIXIV_URL})
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    job = db_session.get(TranslationJob, body["job_id"])
    pages = PageRepository(db_session).list_pages(job_id=body["job_id"])

    assert response.status_code == 200
    assert body["translated_text"] == ""
    assert body["chunks"] == [
        {"index": 0, "source_lang": "ja", "target_lang": "ko", "status": "failed"}
    ]
    assert job is not None
    assert job.status == "failed"
    assert job.failed_chunks == 1
    assert job.error_message == "model exploded"
    assert pages[0].status == "failed"
    assert pages[0].failed_chunks == 1


def test_fetch_translate_rejects_invalid_pixiv_url(db_session: Session) -> None:
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_fetch_service] = lambda: FetchService(
        db_session,
        pixiv_client=FakePixivClient(),
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/api/fetch/pixiv/translate",
            json={"url": "https://www.pixiv.net/novel/series/1234567"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == INVALID_PIXIV_URL_MESSAGE
    assert db_session.query(TranslationJob).count() == 0


def test_fetch_translate_uses_selected_glossary_hash_for_cache(
    db_session: Session,
) -> None:
    GlossaryRepository(db_session).create_term(
        source_term="\u9b54\u738b",
        target_term="\ub9c8\uc655",
        priority=100,
    )
    fake_ollama = FakeOllamaClient(["cached glossary translation"])
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_fetch_service] = lambda: FetchService(
        db_session,
        pixiv_client=FakePixivClient(text=FIRST_PAGE),
        translation_service=TranslationService(db_session, ollama_client=fake_ollama),
    )

    try:
        client = TestClient(app)
        first = client.post("/api/fetch/pixiv/translate", json={"url": PIXIV_URL})
        second = client.post("/api/fetch/pixiv/translate", json={"url": PIXIV_URL})
    finally:
        app.dependency_overrides.clear()

    cache_entry = db_session.query(TranslationCache).one()

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["translated_text"] == "cached glossary translation"
    assert len(fake_ollama.calls) == 1
    assert cache_entry.glossary_hash is not None
    assert cache_entry.glossary_hash != ""
    assert cache_entry.hit_count == 1


def _override_db(db_session: Session):
    def _get_db() -> Generator[Session, None, None]:
        yield db_session

    return _get_db
