from __future__ import annotations

from collections.abc import Generator
from types import SimpleNamespace
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.translate import get_translation_service
from app.db.repositories.cache_repository import CacheRepository
from app.db.repositories.chunk_repository import ChunkRepository
from app.db.repositories.page_repository import PageRepository
from app.db.repositories.translation_repository import TranslationRepository
from app.db.session import get_db
from app.llm.translator import TranslationService
from app.main import app
from app.services.cache import build_cache_key
from app.services.glossary import make_selected_glossary_hash


def test_retry_failed_chunk_success_updates_counts_and_retry_count(
    db_session: Session,
) -> None:
    job, page = _create_job_with_failed_chunk(db_session)
    fake_client = FakeOllamaClient(["retried translation"])
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_translation_service] = lambda: TranslationService(
        db_session,
        ollama_client=fake_client,
    )

    try:
        response = TestClient(app).post(f"/api/translations/{job.id}/chunks/1/retry")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["translated_text"] == "completed translation\n\nretried translation"
    assert payload["chunks"] == [
        {"index": 0, "source_lang": "ja", "target_lang": "ko", "status": "completed"},
        {"index": 1, "source_lang": "ja", "target_lang": "ko", "status": "completed"},
    ]
    assert payload["cache_hit"] is False
    assert len(fake_client.calls) == 1

    retried = ChunkRepository(db_session).get_chunk(
        job_id=job.id,
        page_id=page.id,
        chunk_index=1,
    )
    assert retried is not None
    assert retried.status == "completed"
    assert retried.retry_count == 2
    assert retried.translated_text == "retried translation"
    assert retried.error_message is None

    db_session.refresh(page)
    db_session.refresh(job)
    assert page.status == "completed"
    assert page.completed_chunks == 2
    assert page.failed_chunks == 0
    assert job.status == "completed"
    assert job.completed_chunks == 2
    assert job.failed_chunks == 0
    assert job.error_message is None


def test_retry_completed_chunk_is_rejected(db_session: Session) -> None:
    job, _page = _create_completed_job(db_session)
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_translation_service] = lambda: TranslationService(
        db_session,
        ollama_client=FakeOllamaClient(["unused"]),
    )

    try:
        response = TestClient(app).post(f"/api/translations/{job.id}/chunks/0/retry")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400


def test_retry_failed_chunk_uses_cache_without_llm_call(db_session: Session) -> None:
    job, page = _create_job_with_failed_chunk(db_session)
    source_text = "failed source"
    selected_glossary_hash = make_selected_glossary_hash([])
    cache_key = build_cache_key(
        source_text=source_text,
        source_lang="ja",
        target_lang="ko",
        model_name=job.model_name,
        prompt_version=job.prompt_version,
        style=job.style,
        honorific_policy=job.honorific_policy,
        preserve_names=bool(job.preserve_names),
        selected_glossary_hash=selected_glossary_hash,
    )
    CacheRepository(db_session).create_cache_entry(
        cache_key=cache_key,
        source_text=source_text,
        translated_text="cached retry",
        model_name=job.model_name,
        prompt_version=job.prompt_version,
        style=job.style,
        honorific_policy=job.honorific_policy,
        preserve_names=bool(job.preserve_names),
        selected_glossary_hash=selected_glossary_hash,
    )
    fake_client = FakeOllamaClient(["unused"])
    app.dependency_overrides[get_db] = _override_db(db_session)
    app.dependency_overrides[get_translation_service] = lambda: TranslationService(
        db_session,
        ollama_client=fake_client,
    )

    try:
        response = TestClient(app).post(f"/api/translations/{job.id}/chunks/1/retry")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["cache_hit"] is True
    assert response.json()["translated_text"] == "completed translation\n\ncached retry"
    assert len(fake_client.calls) == 0

    retried = ChunkRepository(db_session).get_chunk(
        job_id=job.id,
        page_id=page.id,
        chunk_index=1,
    )
    assert retried is not None
    assert retried.status == "completed"
    assert retried.retry_count == 2


def _create_job_with_failed_chunk(db_session: Session):
    job = TranslationRepository(db_session).create_job(
        original_text="completed source\n\nfailed source",
        translated_text="completed translation",
        status="partial_failed",
        total_chunks=2,
        completed_chunks=1,
        failed_chunks=1,
        error_message="model timeout",
    )
    page = PageRepository(db_session).create_page(
        job_id=job.id,
        page_index=0,
        source_text="completed source\n\nfailed source",
        translated_text="completed translation",
        status="partial_failed",
        total_chunks=2,
        completed_chunks=1,
        failed_chunks=1,
        error_message="model timeout",
    )
    chunk_repository = ChunkRepository(db_session)
    chunk_repository.create_chunk(
        job_id=job.id,
        page_id=page.id,
        chunk_index=0,
        source_text="completed source",
        translated_text="completed translation",
        status="completed",
    )
    chunk_repository.create_chunk(
        job_id=job.id,
        page_id=page.id,
        chunk_index=1,
        source_text="failed source",
        status="failed",
        retry_count=1,
        error_message="model timeout",
    )
    return job, page


def _create_completed_job(db_session: Session):
    job = TranslationRepository(db_session).create_job(
        original_text="completed source",
        translated_text="completed translation",
        status="completed",
        total_chunks=1,
        completed_chunks=1,
    )
    page = PageRepository(db_session).create_page(
        job_id=job.id,
        page_index=0,
        source_text="completed source",
        translated_text="completed translation",
        status="completed",
        total_chunks=1,
        completed_chunks=1,
    )
    ChunkRepository(db_session).create_chunk(
        job_id=job.id,
        page_id=page.id,
        chunk_index=0,
        source_text="completed source",
        translated_text="completed translation",
        status="completed",
    )
    return job, page


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
