from __future__ import annotations

from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import (
    GlossaryTerm,
    TranslationCache,
    TranslationChunk,
    TranslationFeedback,
    TranslationJob,
    TranslationPage,
)
from app.db.repositories.cache_repository import CacheRepository
from app.db.repositories.chunk_repository import ChunkRepository
from app.db.repositories.feedback_repository import TranslationFeedbackRepository
from app.db.repositories.glossary_repository import GlossaryRepository
from app.db.repositories.page_repository import PageRepository
from app.db.repositories.translation_repository import TranslationRepository
from app.db.session import get_db
from app.main import app


def test_clear_translation_cache_deletes_only_cache_rows(db_session: Session) -> None:
    job = TranslationRepository(db_session).create_job(
        original_text="source",
        translated_text="translated",
        status="completed",
    )
    page = PageRepository(db_session).create_page(
        job_id=job.id,
        page_index=0,
        source_text="source",
        translated_text="translated",
        status="completed",
    )
    chunk = ChunkRepository(db_session).create_chunk(
        job_id=job.id,
        page_id=page.id,
        chunk_index=0,
        source_text="source",
        translated_text="translated",
        status="completed",
    )
    TranslationFeedbackRepository(db_session).create_feedback(
        job_id=job.id,
        chunk_id=chunk.id,
        source_text="source",
        model_translation="translated",
        user_corrected_translation="edited",
        feedback_type="manual_edit",
    )
    GlossaryRepository(db_session).create_term(
        source_term="source term",
        target_term="target term",
    )
    cache_repository = CacheRepository(db_session)
    cache_repository.create_cache_entry(
        cache_key="cache-key-a",
        source_text="source a",
        translated_text="translated a",
    )
    cache_repository.create_cache_entry(
        cache_key="cache-key-b",
        source_text="source b",
        translated_text="translated b",
    )

    app.dependency_overrides[get_db] = _override_db(db_session)
    try:
        response = TestClient(app).delete("/api/cache/translations")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert response.content == b""
    assert db_session.query(TranslationCache).count() == 0
    assert db_session.query(TranslationJob).count() == 1
    assert db_session.query(TranslationPage).count() == 1
    assert db_session.query(TranslationChunk).count() == 1
    assert db_session.query(TranslationFeedback).count() == 1
    assert db_session.query(GlossaryTerm).count() == 1


def test_clear_translation_cache_is_idempotent(db_session: Session) -> None:
    app.dependency_overrides[get_db] = _override_db(db_session)
    try:
        client = TestClient(app)
        first_response = client.delete("/api/cache/translations")
        second_response = client.delete("/api/cache/translations")
    finally:
        app.dependency_overrides.clear()

    assert first_response.status_code == 204
    assert first_response.content == b""
    assert second_response.status_code == 204
    assert second_response.content == b""


def _override_db(db_session: Session):
    def _get_db() -> Generator[Session, None, None]:
        yield db_session

    return _get_db
