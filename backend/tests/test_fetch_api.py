import asyncio
import json
from collections.abc import Generator
from types import SimpleNamespace
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.fetch import get_fetch_service
from app.crawler.pixiv_client import PixivFetchFailedError
from app.crawler.pixiv_types import PIXIV_FETCH_FAILED_MESSAGE, PixivFetchedPage
from app.crawler.url_validator import INVALID_PIXIV_URL_MESSAGE
from app.db.models import TranslationJob
from app.db.repositories.chunk_repository import ChunkRepository
from app.db.session import get_db
from app.llm.translator import TranslationService
from app.main import app
from app.services.fetch_service import FetchService


TITLE = "\u4f5c\u54c1\u30bf\u30a4\u30c8\u30eb"
AUTHOR = "\u4f5c\u8005\u540d"
TEXT = "\u5c0f\u8aac\u672c\u6587...\n\n\u7d9a\u304d\u3002"

PIXIV_PAYLOAD = {
    "novel": {
        "12345678": {
            "title": TITLE,
            "userName": AUTHOR,
            "content": TEXT,
        }
    }
}
PIXIV_HTML = (
    '<html><head><meta id="meta-preload-data" content=\''
    + json.dumps(PIXIV_PAYLOAD, ensure_ascii=True)
    + "'></head><body></body></html>"
)


class FakePixivClient:
    def __init__(self, html: str = PIXIV_HTML) -> None:
        self.html = html
        self.urls: list[str] = []

    async def fetch_html(self, url: str) -> PixivFetchedPage:
        self.urls.append(url)
        return PixivFetchedPage(url=url, html=self.html, status_code=200)


class FailingPixivClient:
    async def fetch_html(self, url: str) -> PixivFetchedPage:
        raise PixivFetchFailedError(PIXIV_FETCH_FAILED_MESSAGE)


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


def test_fetch_service_saves_pixiv_result_to_translation_jobs(
    db_session: Session,
) -> None:
    async def run_test() -> None:
        service = FetchService(db_session, pixiv_client=FakePixivClient())

        result = await service.fetch_pixiv(
            url="https://www.pixiv.net/novel/show.php?id=12345678",
            translate_after_fetch=False,
        )

        saved = db_session.get(TranslationJob, result.job_id)

        assert result.source_site == "pixiv"
        assert result.source_url == "https://www.pixiv.net/novel/show.php?id=12345678"
        assert result.source_work_id == "12345678"
        assert result.title == TITLE
        assert result.author == AUTHOR
        assert result.text == TEXT
        assert result.char_count == len(TEXT)
        assert saved is not None
        assert saved.source_site == "pixiv"
        assert saved.source_url == result.source_url
        assert saved.source_title == TITLE
        assert saved.source_author == AUTHOR
        assert saved.source_work_id == "12345678"
        assert saved.original_text == result.text
        assert saved.status == "fetched"
        assert saved.ollama_think == "false"
        assert saved.ollama_options_json is None

    asyncio.run(run_test())


def test_fetch_pixiv_api_returns_saved_result(db_session: Session) -> None:
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_fetch_service] = lambda: FetchService(
        db_session,
        pixiv_client=FakePixivClient(),
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/api/fetch/pixiv",
            json={
                "url": "https://www.pixiv.net/novel/show.php?id=12345678",
                "translate_after_fetch": False,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "source_site": "pixiv",
        "source_url": "https://www.pixiv.net/novel/show.php?id=12345678",
        "source_work_id": "12345678",
        "title": TITLE,
        "author": AUTHOR,
        "text": TEXT,
        "char_count": len(TEXT),
        "job_id": 1,
    }


def test_fetch_pixiv_translate_api_returns_translation_result(db_session: Session) -> None:
    translation_service = TranslationService(
        db_session,
        ollama_client=FakeOllamaClient(["translated pixiv text"]),
    )
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_fetch_service] = lambda: FetchService(
        db_session,
        pixiv_client=FakePixivClient(),
        translation_service=translation_service,
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/api/fetch/pixiv/translate",
            json={
                "url": "https://www.pixiv.net/novel/show.php?id=12345678",
                "style": "webnovel",
                "honorific_policy": "preserve",
                "preserve_names": True,
                "use_glossary": True,
                "use_cache": True,
                "think": "low",
                "options": {"temperature": 0.2, "max_tokens": 2048},
            },
        )
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    saved = db_session.get(TranslationJob, body["job_id"])
    chunks = ChunkRepository(db_session).list_chunks(job_id=body["job_id"])

    assert response.status_code == 200
    assert body["job_id"] == 1
    assert body["source_site"] == "pixiv"
    assert body["source_url"] == "https://www.pixiv.net/novel/show.php?id=12345678"
    assert body["source_work_id"] == "12345678"
    assert body["title"] == TITLE
    assert body["author"] == AUTHOR
    assert body["translated_text"] == "translated pixiv text"
    assert body["chunks"] == [
        {"index": 0, "source_lang": "ja", "target_lang": "ko", "status": "completed"}
    ]
    assert saved is not None
    assert saved.source_site == "pixiv"
    assert saved.status == "completed"
    assert saved.translated_text == "translated pixiv text"
    assert saved.ollama_think == '"low"'
    assert saved.ollama_options_json == '{"max_tokens": 2048, "temperature": 0.2}'
    assert len(chunks) == 1
    assert chunks[0].status == "completed"


def test_fetch_pixiv_api_accepts_ollama_options(db_session: Session) -> None:
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_fetch_service] = lambda: FetchService(
        db_session,
        pixiv_client=FakePixivClient(),
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/api/fetch/pixiv",
            json={
                "url": "https://www.pixiv.net/novel/show.php?id=12345678",
                "translate_after_fetch": True,
                "think": "low",
                "options": {"temperature": 0.2, "max_tokens": 2048},
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    saved = db_session.get(TranslationJob, 1)
    assert saved is not None
    assert saved.status == "pending_translation"
    assert saved.ollama_think == '"low"'
    assert saved.ollama_options_json == '{"max_tokens": 2048, "temperature": 0.2}'


def test_fetch_pixiv_api_rejects_invalid_ollama_think(db_session: Session) -> None:
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_fetch_service] = lambda: FetchService(
        db_session,
        pixiv_client=FakePixivClient(),
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/api/fetch/pixiv",
            json={
                "url": "https://www.pixiv.net/novel/show.php?id=12345678",
                "think": 1,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_fetch_pixiv_api_rejects_invalid_ollama_options(db_session: Session) -> None:
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_fetch_service] = lambda: FetchService(
        db_session,
        pixiv_client=FakePixivClient(),
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/api/fetch/pixiv",
            json={
                "url": "https://www.pixiv.net/novel/show.php?id=12345678",
                "options": ["temperature", 0.2],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_fetch_pixiv_api_rejects_invalid_url(db_session: Session) -> None:
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_fetch_service] = lambda: FetchService(
        db_session,
        pixiv_client=FakePixivClient(),
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/api/fetch/pixiv",
            json={
                "url": "https://www.pixiv.net/novel/series/1234567",
                "translate_after_fetch": False,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == INVALID_PIXIV_URL_MESSAGE


def test_fetch_pixiv_api_returns_fetch_failure(db_session: Session) -> None:
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_fetch_service] = lambda: FetchService(
        db_session,
        pixiv_client=FailingPixivClient(),
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/api/fetch/pixiv",
            json={
                "url": "https://www.pixiv.net/novel/show.php?id=12345678",
                "translate_after_fetch": False,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json()["detail"] == PIXIV_FETCH_FAILED_MESSAGE


def _override_db(db_session: Session):
    def _get_db() -> Generator[Session, None, None]:
        yield db_session

    return _get_db
