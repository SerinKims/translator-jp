from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import TranslationJob, TranslationPage
from app.services.page_splitter import split_pages


class PageRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_page(
        self,
        *,
        job_id: int,
        page_index: int,
        source_text: str,
        page_title: str | None = None,
        translated_text: str | None = None,
        status: str = "pending",
        total_chunks: int = 0,
        completed_chunks: int = 0,
        failed_chunks: int = 0,
        elapsed_ms: int | None = None,
        error_message: str | None = None,
    ) -> TranslationPage:
        page = TranslationPage(
            job_id=job_id,
            page_index=page_index,
            page_title=page_title,
            source_text=source_text,
            translated_text=translated_text,
            status=status,
            total_chunks=total_chunks,
            completed_chunks=completed_chunks,
            failed_chunks=failed_chunks,
            elapsed_ms=elapsed_ms,
            error_message=error_message,
        )
        self.db.add(page)
        self.db.commit()
        self.db.refresh(page)
        return page

    def ensure_pages_for_job(self, job: TranslationJob) -> list[TranslationPage]:
        pages = self.list_pages(job_id=job.id)
        if pages:
            return pages

        for source_page in split_pages(job.original_text):
            self.create_page(
                job_id=job.id,
                page_index=source_page.page_index,
                page_title=source_page.page_title,
                source_text=source_page.source_text,
            )
        return self.list_pages(job_id=job.id)

    def get_page(self, *, job_id: int, page_index: int) -> TranslationPage | None:
        statement = select(TranslationPage).where(
            TranslationPage.job_id == job_id,
            TranslationPage.page_index == page_index,
        )
        return self.db.scalar(statement)

    def get_page_by_id(self, page_id: int) -> TranslationPage | None:
        return self.db.get(TranslationPage, page_id)

    def list_pages(self, *, job_id: int) -> list[TranslationPage]:
        statement = (
            select(TranslationPage)
            .where(TranslationPage.job_id == job_id)
            .order_by(TranslationPage.page_index)
        )
        return list(self.db.scalars(statement))

    def update_page(
        self,
        page_id: int,
        *,
        translated_text: str | None = None,
        status: str | None = None,
        total_chunks: int | None = None,
        completed_chunks: int | None = None,
        failed_chunks: int | None = None,
        elapsed_ms: int | None = None,
        error_message: str | None = None,
    ) -> TranslationPage | None:
        page = self.get_page_by_id(page_id)
        if page is None:
            return None

        if translated_text is not None:
            page.translated_text = translated_text
        if status is not None:
            page.status = status
        if total_chunks is not None:
            page.total_chunks = total_chunks
        if completed_chunks is not None:
            page.completed_chunks = completed_chunks
        if failed_chunks is not None:
            page.failed_chunks = failed_chunks
        if elapsed_ms is not None:
            page.elapsed_ms = elapsed_ms
        if error_message is not None:
            page.error_message = error_message

        self.db.commit()
        self.db.refresh(page)
        return page
