from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import (
    TranslationCache,
    TranslationChunk,
    TranslationFeedback,
    TranslationPage,
)
from app.db.repositories.cache_repository import CacheRepository
from app.db.repositories.chunk_repository import ChunkRepository
from app.db.repositories.page_repository import PageRepository
from app.db.repositories.translation_repository import TranslationRepository


def test_create_translation_job(db_session: Session) -> None:
    repository = TranslationRepository(db_session)

    job = repository.create_job(original_text="吾輩は猫である。")

    assert job.id is not None
    assert job.original_text == "吾輩は猫である。"
    assert job.source_site == "manual"
    assert job.model_name == "gemma4:26b-a4b-it-q4_K_M"
    assert job.prompt_version == "translate_ja_ko_v1"
    assert job.ollama_think == "false"
    assert job.ollama_options_json is None
    assert job.style == "webnovel"
    assert job.honorific_policy == "preserve"
    assert job.preserve_names == 1
    assert job.status == "pending"


def test_create_translation_job_with_pixiv_source_metadata(db_session: Session) -> None:
    repository = TranslationRepository(db_session)
    fetched_at = datetime(2026, 6, 22, 10, 0, 0)

    job = repository.create_job(
        source_site="pixiv",
        source_url="https://www.pixiv.net/novel/show.php?id=12345678",
        source_title="夜の物語",
        source_author="作者名",
        source_work_id="12345678",
        source_fetched_at=fetched_at,
        original_text="これはpixiv小説です。",
    )

    saved = repository.get_job(job.id)

    assert saved is not None
    assert saved.source_site == "pixiv"
    assert saved.source_url == "https://www.pixiv.net/novel/show.php?id=12345678"
    assert saved.source_title == "夜の物語"
    assert saved.source_author == "作者名"
    assert saved.source_work_id == "12345678"
    assert saved.source_fetched_at == fetched_at


def test_create_translation_job_with_ollama_options(db_session: Session) -> None:
    repository = TranslationRepository(db_session)

    job = repository.create_job(
        original_text="原文",
        ollama_think="low",
        ollama_options={"temperature": 0.2, "max_tokens": 2048},
    )

    assert job.ollama_think == '"low"'
    assert job.ollama_options_json == '{"max_tokens": 2048, "temperature": 0.2}'


def test_create_translation_job_with_detected_language_metadata(db_session: Session) -> None:
    repository = TranslationRepository(db_session)

    job = repository.create_job(
        original_text="He closed his eyes.",
        source_language="en",
        target_language="ko",
        detected_lang="en",
        language_confidence=0.95,
    )

    assert job.source_language == "en"
    assert job.target_language == "ko"
    assert job.detected_lang == "en"
    assert job.language_confidence == 0.95


def test_delete_translation_job_cascades_pages_chunks_feedback_and_keeps_cache(
    db_session: Session,
) -> None:
    repository = TranslationRepository(db_session)
    job = repository.create_job(
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
    feedback = TranslationFeedback(
        job_id=job.id,
        chunk_id=chunk.id,
        source_text="source",
        model_translation="translated",
        user_corrected_translation="corrected",
        rating=4,
        feedback_type="quality",
    )
    db_session.add(feedback)
    db_session.commit()
    db_session.refresh(feedback)
    feedback_id = feedback.id
    cache_entry = CacheRepository(db_session).create_cache_entry(
        cache_key="cache-key",
        source_text="source",
        translated_text="translated",
    )

    assert repository.delete_job(job.id) is True

    assert repository.get_job(job.id) is None
    assert db_session.get(TranslationPage, page.id) is None
    assert db_session.get(TranslationChunk, chunk.id) is None
    assert db_session.get(TranslationFeedback, feedback_id) is None
    assert db_session.get(TranslationCache, cache_entry.id) is not None


def test_delete_translation_job_returns_false_for_missing_job(db_session: Session) -> None:
    repository = TranslationRepository(db_session)

    assert repository.delete_job(999) is False


def test_delete_all_translation_jobs_removes_all_jobs_and_keeps_cache(
    db_session: Session,
) -> None:
    repository = TranslationRepository(db_session)
    first = repository.create_job(original_text="first")
    second = repository.create_job(original_text="second")
    linked_feedback = TranslationFeedback(
        job_id=first.id,
        source_text="source",
        model_translation="translated",
        user_corrected_translation="corrected",
        feedback_type="quality",
    )
    orphan_feedback = TranslationFeedback(
        source_text="orphan source",
        model_translation="orphan translated",
        user_corrected_translation="orphan corrected",
        feedback_type="quality",
    )
    db_session.add_all([linked_feedback, orphan_feedback])
    db_session.commit()
    cache_entry = CacheRepository(db_session).create_cache_entry(
        cache_key="cache-key",
        source_text="source",
        translated_text="translated",
    )

    assert repository.delete_all_jobs() == 2

    assert repository.get_job(first.id) is None
    assert repository.get_job(second.id) is None
    assert db_session.query(TranslationFeedback).count() == 0
    assert db_session.get(TranslationCache, cache_entry.id) is not None
