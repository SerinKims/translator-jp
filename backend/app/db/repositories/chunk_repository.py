from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import TranslationChunk, TranslationJob
from app.db.repositories.page_repository import PageRepository


class ChunkRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_chunk(
        self,
        *,
        job_id: int,
        chunk_index: int,
        source_text: str,
        page_id: int | None = None,
        page_index: int = 0,
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
        resolved_page_id = self._resolve_page_id(
            job_id=job_id,
            page_id=page_id,
            page_index=page_index,
        )
        existing = self.get_chunk(
            job_id=job_id,
            chunk_index=chunk_index,
            page_id=resolved_page_id,
        )
        if existing is not None:
            existing.source_text = source_text
            existing.context_before = context_before
            existing.context_after = context_after
            existing.status = status
            existing.translated_text = translated_text
            existing.prompt_used = prompt_used
            existing.raw_model_response = raw_model_response
            existing.elapsed_ms = elapsed_ms
            existing.error_message = error_message
            self.db.commit()
            self.db.refresh(existing)
            return existing

        chunk = TranslationChunk(
            job_id=job_id,
            page_id=resolved_page_id,
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

    def get_chunk(
        self,
        *,
        job_id: int,
        chunk_index: int,
        page_id: int | None = None,
        page_index: int | None = None,
    ) -> TranslationChunk | None:
        statement = select(TranslationChunk).where(TranslationChunk.job_id == job_id)
        if page_id is not None:
            statement = statement.where(TranslationChunk.page_id == page_id)
        elif page_index is not None:
            page = PageRepository(self.db).get_page(job_id=job_id, page_index=page_index)
            if page is None:
                return None
            statement = statement.where(TranslationChunk.page_id == page.id)
        statement = statement.where(TranslationChunk.chunk_index == chunk_index)
        return self.db.scalar(statement)

    def list_chunks(
        self,
        *,
        job_id: int,
        page_id: int | None = None,
        page_index: int | None = None,
    ) -> list[TranslationChunk]:
        statement = (
            select(TranslationChunk)
            .where(TranslationChunk.job_id == job_id)
            .order_by(TranslationChunk.page_id, TranslationChunk.chunk_index)
        )
        if page_id is not None:
            statement = statement.where(TranslationChunk.page_id == page_id)
        elif page_index is not None:
            page = PageRepository(self.db).get_page(job_id=job_id, page_index=page_index)
            if page is None:
                return []
            statement = statement.where(TranslationChunk.page_id == page.id)
        return list(self.db.scalars(statement))

    def update_status(
        self,
        *,
        job_id: int,
        chunk_index: int,
        page_id: int | None = None,
        page_index: int | None = None,
        status: str,
        translated_text: str | None = None,
        raw_model_response: str | None = None,
        elapsed_ms: int | None = None,
        error_message: str | None = None,
        increment_retry_count: bool = False,
    ) -> TranslationChunk | None:
        chunk = self.get_chunk(
            job_id=job_id,
            chunk_index=chunk_index,
            page_id=page_id,
            page_index=page_index,
        )
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

    def _resolve_page_id(
        self,
        *,
        job_id: int,
        page_id: int | None,
        page_index: int,
    ) -> int:
        if page_id is not None:
            return page_id

        job = self.db.get(TranslationJob, job_id)
        if job is None:
            raise ValueError(f"translation job not found: {job_id}")

        page_repository = PageRepository(self.db)
        pages = page_repository.ensure_pages_for_job(job)
        for page in pages:
            if page.page_index == page_index:
                return page.id
        raise ValueError(f"translation page not found: job_id={job_id}, page_index={page_index}")
