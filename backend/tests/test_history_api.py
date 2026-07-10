from __future__ import annotations

from collections.abc import Generator
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import TranslationFeedback
from app.db.repositories.cache_repository import CacheRepository
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


def test_update_page_translation_replaces_final_text_and_keeps_model_records(
    db_session: Session,
) -> None:
    job = TranslationRepository(db_session).create_job(
        original_text="page one[newpage]page two",
        translated_text="model page one\n\nmodel page two",
        status="completed",
        total_chunks=2,
        completed_chunks=2,
    )
    page_repository = PageRepository(db_session)
    first_page = page_repository.create_page(
        job_id=job.id,
        page_index=0,
        source_text="page one",
        translated_text="model page one",
        status="completed",
        total_chunks=1,
        completed_chunks=1,
    )
    page_repository.create_page(
        job_id=job.id,
        page_index=1,
        source_text="page two",
        translated_text="model page two",
        status="completed",
        total_chunks=1,
        completed_chunks=1,
    )
    chunk = ChunkRepository(db_session).create_chunk(
        job_id=job.id,
        page_id=first_page.id,
        chunk_index=0,
        source_text="page one",
        translated_text="model page one",
        status="completed",
    )
    cache_entry = CacheRepository(db_session).create_cache_entry(
        cache_key="cache-key",
        source_text="page one",
        translated_text="model page one",
    )

    app.dependency_overrides[get_db] = _override_db(db_session)
    try:
        response = TestClient(app).patch(
            f"/api/translations/{job.id}/pages/0/translation",
            json={"translated_text": "edited page one", "comment": "manual polish"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["translated_text"] == "edited page one\n\nmodel page two"
    assert payload["translated_preview"].startswith("edited page one")
    assert payload["pages"][0]["translated_text"] == "edited page one"
    assert payload["pages"][1]["translated_text"] == "model page two"

    db_session.refresh(job)
    db_session.refresh(first_page)
    db_session.refresh(chunk)
    db_session.refresh(cache_entry)
    assert job.translated_text == "edited page one\n\nmodel page two"
    assert first_page.translated_text == "edited page one"
    assert chunk.translated_text == "model page one"
    assert cache_entry.translated_text == "model page one"

    feedback_rows = db_session.query(TranslationFeedback).all()
    assert len(feedback_rows) == 1
    feedback = feedback_rows[0]
    assert feedback.job_id == job.id
    assert feedback.chunk_id is None
    assert feedback.source_text == "page one"
    assert feedback.model_translation == "model page one"
    assert feedback.user_corrected_translation == "edited page one"
    assert feedback.feedback_type == "manual_edit"
    assert feedback.comment == "manual polish"


def test_update_page_translation_returns_404_for_missing_job(db_session: Session) -> None:
    app.dependency_overrides[get_db] = _override_db(db_session)
    try:
        response = TestClient(app).patch(
            "/api/translations/999/pages/0/translation",
            json={"translated_text": "edited"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_update_page_translation_returns_404_for_missing_page(db_session: Session) -> None:
    job = TranslationRepository(db_session).create_job(
        original_text="source",
        translated_text="translated",
        status="completed",
    )

    app.dependency_overrides[get_db] = _override_db(db_session)
    try:
        response = TestClient(app).patch(
            f"/api/translations/{job.id}/pages/1/translation",
            json={"translated_text": "edited"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_update_page_translation_returns_409_for_unfinished_page(
    db_session: Session,
) -> None:
    job = TranslationRepository(db_session).create_job(
        original_text="source",
        status="running",
    )
    PageRepository(db_session).create_page(
        job_id=job.id,
        page_index=0,
        source_text="source",
        status="running",
    )

    app.dependency_overrides[get_db] = _override_db(db_session)
    try:
        response = TestClient(app).patch(
            f"/api/translations/{job.id}/pages/0/translation",
            json={"translated_text": "edited"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409


def test_update_page_translation_returns_422_for_blank_text(
    db_session: Session,
) -> None:
    job = TranslationRepository(db_session).create_job(
        original_text="source",
        translated_text="translated",
        status="completed",
    )
    PageRepository(db_session).create_page(
        job_id=job.id,
        page_index=0,
        source_text="source",
        translated_text="translated",
        status="completed",
    )

    app.dependency_overrides[get_db] = _override_db(db_session)
    try:
        response = TestClient(app).patch(
            f"/api/translations/{job.id}/pages/0/translation",
            json={"translated_text": "   "},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_delete_translation_removes_job_from_history(db_session: Session) -> None:
    job = TranslationRepository(db_session).create_job(
        original_text="source",
        translated_text="translated",
        status="completed",
    )
    feedback = TranslationFeedback(
        job_id=job.id,
        source_text="source",
        model_translation="translated",
        user_corrected_translation="corrected",
        feedback_type="manual_edit",
    )
    db_session.add(feedback)
    db_session.commit()
    feedback_id = feedback.id

    app.dependency_overrides[get_db] = _override_db(db_session)
    try:
        client = TestClient(app)
        delete_response = client.delete(f"/api/translations/{job.id}")
        detail_response = client.get(f"/api/translations/{job.id}")
        list_response = client.get("/api/translations")
    finally:
        app.dependency_overrides.clear()

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert detail_response.status_code == 404
    assert list_response.status_code == 200
    assert list_response.json() == []
    assert db_session.get(TranslationFeedback, feedback_id) is None


def test_delete_translation_returns_404_for_missing_job(db_session: Session) -> None:
    app.dependency_overrides[get_db] = _override_db(db_session)
    try:
        response = TestClient(app).delete("/api/translations/999")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_delete_all_translations_clears_history_and_is_idempotent(db_session: Session) -> None:
    repository = TranslationRepository(db_session)
    first = repository.create_job(original_text="first", status="completed")
    second = repository.create_job(original_text="second", status="failed")
    db_session.add_all(
        [
            TranslationFeedback(
                job_id=first.id,
                source_text="first",
                model_translation="translated first",
                user_corrected_translation="corrected first",
                feedback_type="manual_edit",
            ),
            TranslationFeedback(
                job_id=second.id,
                source_text="second",
                model_translation="translated second",
                user_corrected_translation="corrected second",
                feedback_type="manual_edit",
            ),
        ]
    )
    db_session.commit()

    app.dependency_overrides[get_db] = _override_db(db_session)
    try:
        client = TestClient(app)
        first_delete_response = client.delete("/api/translations")
        second_delete_response = client.delete("/api/translations")
        list_response = client.get("/api/translations")
    finally:
        app.dependency_overrides.clear()

    assert first_delete_response.status_code == 204
    assert first_delete_response.content == b""
    assert second_delete_response.status_code == 204
    assert second_delete_response.content == b""
    assert list_response.status_code == 200
    assert list_response.json() == []
    assert db_session.query(TranslationFeedback).count() == 0


def _override_db(db_session: Session):
    def _get_db() -> Generator[Session, None, None]:
        yield db_session

    return _get_db
