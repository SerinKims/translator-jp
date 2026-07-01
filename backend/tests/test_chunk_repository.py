from sqlalchemy.orm import Session

from app.db.repositories.chunk_repository import ChunkRepository
from app.db.repositories.translation_repository import TranslationRepository


def test_create_translation_chunk(db_session: Session) -> None:
    job = TranslationRepository(db_session).create_job(original_text="長い小説の本文です。")
    repository = ChunkRepository(db_session)

    chunk = repository.create_chunk(
        job_id=job.id,
        chunk_index=0,
        source_text="長い小説の本文です。",
        context_before="",
        context_after="次の段落",
        prompt_used="translate_ja_ko_v1 prompt",
    )

    assert chunk.id is not None
    assert chunk.job_id == job.id
    assert chunk.chunk_index == 0
    assert chunk.source_lang == "ja"
    assert chunk.target_lang == "ko"
    assert chunk.source_text == "長い小説の本文です。"
    assert chunk.status == "pending"
    assert chunk.retry_count == 0
    assert chunk.prompt_used == "translate_ja_ko_v1 prompt"


def test_update_chunk_status(db_session: Session) -> None:
    job = TranslationRepository(db_session).create_job(original_text="第一話。")
    repository = ChunkRepository(db_session)
    repository.create_chunk(job_id=job.id, chunk_index=0, source_text="第一話。")

    updated = repository.update_status(
        job_id=job.id,
        chunk_index=0,
        status="completed",
        translated_text="제1화.",
        raw_model_response='{"message":"ok"}',
        elapsed_ms=120,
    )

    assert updated is not None
    assert updated.status == "completed"
    assert updated.translated_text == "제1화."
    assert updated.raw_model_response == '{"message":"ok"}'
    assert updated.elapsed_ms == 120


def test_update_failed_chunk_increments_retry_count(db_session: Session) -> None:
    job = TranslationRepository(db_session).create_job(original_text="第二話。")
    repository = ChunkRepository(db_session)
    repository.create_chunk(job_id=job.id, chunk_index=0, source_text="第二話。")

    updated = repository.update_status(
        job_id=job.id,
        chunk_index=0,
        status="failed",
        error_message="model timeout",
        increment_retry_count=True,
    )

    assert updated is not None
    assert updated.status == "failed"
    assert updated.error_message == "model timeout"
    assert updated.retry_count == 1


def test_create_translation_chunk_with_language_pair(db_session: Session) -> None:
    job = TranslationRepository(db_session).create_job(
        original_text="He closed his eyes.",
        source_language="en",
    )
    repository = ChunkRepository(db_session)

    chunk = repository.create_chunk(
        job_id=job.id,
        chunk_index=0,
        source_lang="en",
        target_lang="ko",
        source_text="He closed his eyes.",
    )

    assert chunk.source_lang == "en"
    assert chunk.target_lang == "ko"
