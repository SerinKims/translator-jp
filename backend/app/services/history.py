from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import TranslationChunk, TranslationJob, TranslationPage
from app.db.repositories.chunk_repository import ChunkRepository
from app.db.repositories.page_repository import PageRepository
from app.db.repositories.translation_repository import TranslationRepository
from app.schemas.translation import (
    TranslationChunkHistory,
    TranslationDetailResponse,
    TranslationHistoryItem,
    TranslationPageHistory,
)
from app.services.page_splitter import split_pages

JOB_NOT_FOUND_MESSAGE = "Translation job not found."
PREVIEW_CHARS = 160


class HistoryServiceError(RuntimeError):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class HistoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.translation_repository = TranslationRepository(db)
        self.page_repository = PageRepository(db)
        self.chunk_repository = ChunkRepository(db)

    def list_translations(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TranslationHistoryItem]:
        jobs = self.translation_repository.list_jobs(limit=limit, offset=offset)
        return [self._job_to_history_item(job) for job in jobs]

    def get_translation_detail(self, job_id: int) -> TranslationDetailResponse:
        job = self.translation_repository.get_job(job_id)
        if job is None:
            raise HistoryServiceError(JOB_NOT_FOUND_MESSAGE, status_code=404)

        pages = self.page_repository.list_pages(job_id=job.id)
        chunks = self.chunk_repository.list_chunks(job_id=job.id)
        page_indexes = {page.id: page.page_index for page in pages}
        base = self._job_to_history_item(job)
        return TranslationDetailResponse(
            **base.model_dump(),
            original_text=job.original_text,
            translated_text=job.translated_text,
            pages=[self._page_to_history(page) for page in pages],
            chunks=[
                self._chunk_to_history(chunk, page_index=page_indexes.get(chunk.page_id))
                for chunk in chunks
            ],
        )

    def _job_to_history_item(self, job: TranslationJob) -> TranslationHistoryItem:
        return TranslationHistoryItem(
            job_id=job.id,
            source_site=job.source_site,
            source_url=job.source_url,
            source_title=job.source_title,
            source_author=job.source_author,
            source_work_id=job.source_work_id,
            source_fetched_at=job.source_fetched_at,
            source_preview=_preview(job.original_text),
            translated_preview=_preview(job.translated_text),
            source_lang=job.source_language,
            target_lang=job.target_language,
            model_name=job.model_name,
            prompt_version=job.prompt_version,
            ollama_think=job.ollama_think,
            ollama_options_json=job.ollama_options_json,
            style=job.style,
            honorific_policy=job.honorific_policy,
            preserve_names=bool(job.preserve_names),
            status=job.status,
            total_pages=self._total_pages(job),
            total_chunks=job.total_chunks,
            completed_chunks=job.completed_chunks,
            failed_chunks=job.failed_chunks,
            elapsed_ms=job.elapsed_ms,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )

    def _page_to_history(self, page: TranslationPage) -> TranslationPageHistory:
        return TranslationPageHistory(
            id=page.id,
            page_index=page.page_index,
            page_title=page.page_title,
            source_text=page.source_text,
            translated_text=page.translated_text,
            status=page.status,
            total_chunks=page.total_chunks,
            completed_chunks=page.completed_chunks,
            failed_chunks=page.failed_chunks,
            elapsed_ms=page.elapsed_ms,
            error_message=page.error_message,
            created_at=page.created_at,
            updated_at=page.updated_at,
        )

    def _chunk_to_history(
        self,
        chunk: TranslationChunk,
        *,
        page_index: int | None,
    ) -> TranslationChunkHistory:
        return TranslationChunkHistory(
            id=chunk.id,
            page_id=chunk.page_id,
            page_index=page_index,
            chunk_index=chunk.chunk_index,
            source_text=chunk.source_text,
            translated_text=chunk.translated_text,
            context_before=chunk.context_before,
            context_after=chunk.context_after,
            status=chunk.status,
            retry_count=chunk.retry_count,
            prompt_used=chunk.prompt_used,
            raw_model_response=chunk.raw_model_response,
            elapsed_ms=chunk.elapsed_ms,
            error_message=chunk.error_message,
            created_at=chunk.created_at,
            updated_at=chunk.updated_at,
        )

    def _total_pages(self, job: TranslationJob) -> int:
        saved_pages = self.page_repository.list_pages(job_id=job.id)
        if saved_pages:
            return len(saved_pages)
        return len(split_pages(job.original_text))


def _preview(text: str | None, *, limit: int = PREVIEW_CHARS) -> str | None:
    if text is None:
        return None
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit].rstrip()}..."
