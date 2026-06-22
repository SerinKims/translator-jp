from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import TranslationChunk


class ChunkRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_chunk(
        self,
        *,
        job_id: int,
        chunk_index: int,
        source_text: str,
        translated_text: str | None = None,
        context_before: str | None = None,
        context_after: str | None = None,
        status: str = "pending",
        retry_count: int = 0,
        prompt_used: str | None = None,
        raw_model_response: str | None = None,
        elapsed_ms: int | None = None,
        error_message: str | None = None,
    ) -> TranslationChunk:
        chunk = TranslationChunk(
            job_id=job_id,
            chunk_index=chunk_index,
            source_text=source_text,
            translated_text=translated_text,
            context_before=context_before,
            context_after=context_after,
            status=status,
            retry_count=retry_count,
            prompt_used=prompt_used,
            raw_model_response=raw_model_response,
            elapsed_ms=elapsed_ms,
            error_message=error_message,
        )
        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)
        return chunk

    def get_chunk(self, *, job_id: int, chunk_index: int) -> TranslationChunk | None:
        statement = select(TranslationChunk).where(
            TranslationChunk.job_id == job_id,
            TranslationChunk.chunk_index == chunk_index,
        )
        return self.db.scalar(statement)

    def list_chunks(self, *, job_id: int) -> list[TranslationChunk]:
        statement = (
            select(TranslationChunk)
            .where(TranslationChunk.job_id == job_id)
            .order_by(TranslationChunk.chunk_index)
        )
        return list(self.db.scalars(statement))

    def update_status(
        self,
        *,
        job_id: int,
        chunk_index: int,
        status: str,
        translated_text: str | None = None,
        raw_model_response: str | None = None,
        elapsed_ms: int | None = None,
        error_message: str | None = None,
        increment_retry_count: bool = False,
    ) -> TranslationChunk | None:
        chunk = self.get_chunk(job_id=job_id, chunk_index=chunk_index)
        if chunk is None:
            return None

        chunk.status = status
        if translated_text is not None:
            chunk.translated_text = translated_text
        if raw_model_response is not None:
            chunk.raw_model_response = raw_model_response
        if elapsed_ms is not None:
            chunk.elapsed_ms = elapsed_ms
        if error_message is not None:
            chunk.error_message = error_message
        if increment_retry_count:
            chunk.retry_count += 1

        self.db.commit()
        self.db.refresh(chunk)
        return chunk
