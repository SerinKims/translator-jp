from __future__ import annotations

from collections.abc import Generator
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.repositories.chunk_repository import ChunkRepository
from app.db.repositories.page_repository import PageRepository
from app.db.repositories.translation_repository import TranslationRepository
from app.db.session import get_db
from app.main import app


def test_list_translation_history_returns_latest_first_without_original_text(
    db_session: Session,
) -> None:
    repository = TranslationRepository(db_session)
    older = repository.create_job(
        original_text="old source",
        translated_text="old translated",
        status="completed",
    )
    newer = repository.create_job(
        original_text="new source " * 40,
        source_site="pixiv",
        source_url="https://www.pixiv.net/novel/show.php?id=123",
        source_title="title",
        source_author="author",
        source_work_id="123",
        translated_text="new translated",
        status="completed",
    )
    older.created_at = datetime(2026, 6, 1, 10, 0, 0)
    newer.created_at = datetime(2026, 6, 2, 10, 0, 0)
    db_session.commit()
    PageRepository(db_session).create_page(
        job_id=newer.id,
        page_index=0,
        source_text="new source",
        translated_text="new translated",
        status="completed",
    )

    app.dependency_overrides[get_db] = _override_db(db_session)
    try:
        response = TestClient(app).get("/api/translations")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert [item["job_id"] for item in payload] == [newer.id, older.id]
    assert "original_text" not in payload[0]
    assert payload[0]["source_preview"].startswith("new source")
    assert len(payload[0]["source_preview"]) < len("new source " * 40)
    assert payload[0]["source_site"] == "pixiv"
    assert payload[0]["source_url"] == "https://www.pixiv.net/novel/show.php?id=123"
    assert payload[0]["source_title"] == "title"
    assert payload[0]["source_author"] == "author"
    assert payload[0]["source_work_id"] == "123"
    assert payload[0]["status"] == "completed"
    assert payload[0]["total_pages"] == 1


def test_get_translation_detail_returns_job_pages_and_chunks(db_session: Session) -> None:
    job = TranslationRepository(db_session).create_job(
        original_text="page one[newpage]page two",
        translated_text="translated one",
        status="partial_failed",
        total_chunks=2,
        completed_chunks=1,
        failed_chunks=1,
    )
    page_repository = PageRepository(db_session)
    page = page_repository.create_page(
        job_id=job.id,
        page_index=0,
        source_text="page one",
        translated_text="translated one",
        status="completed",
        total_chunks=1,
        completed_chunks=1,
    )
    ChunkRepository(db_session).create_chunk(
        job_id=job.id,
        page_id=page.id,
        chunk_index=0,
        source_text="page one",
        translated_text="translated one",
        status="completed",
        retry_count=1,
    )

    app.dependency_overrides[get_db] = _override_db(db_session)
    try:
        response = TestClient(app).get(f"/api/translations/{job.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"] == job.id
    assert payload["original_text"] == "page one[newpage]page two"
    assert payload["translated_text"] == "translated one"
    assert payload["total_pages"] == 1
    assert payload["pages"][0]["page_index"] == 0
    assert payload["pages"][0]["source_text"] == "page one"
    assert payload["chunks"][0]["page_index"] == 0
    assert payload["chunks"][0]["chunk_index"] == 0
    assert payload["chunks"][0]["retry_count"] == 1


def test_get_translation_detail_returns_404_for_missing_job(db_session: Session) -> None:
    app.dependency_overrides[get_db] = _override_db(db_session)
    try:
        response = TestClient(app).get("/api/translations/999")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def _override_db(db_session: Session):
    def _get_db() -> Generator[Session, None, None]:
        yield db_session

    return _get_db
