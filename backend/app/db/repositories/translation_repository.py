from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import TranslationJob


class TranslationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_job(
        self,
        *,
        original_text: str,
        source_language: str = "ja",
        target_language: str = "ko",
        source_site: str = "manual",
        source_url: str | None = None,
        source_title: str | None = None,
        source_author: str | None = None,
        source_work_id: str | None = None,
        source_fetched_at: datetime | None = None,
        translated_text: str | None = None,
        model_name: str = "gemma4-e4b",
        prompt_version: str = "translate_ja_ko_v1",
        style: str = "webnovel",
        honorific_policy: str = "preserve",
        preserve_names: bool = True,
        status: str = "pending",
        total_chunks: int = 0,
        completed_chunks: int = 0,
        failed_chunks: int = 0,
        elapsed_ms: int | None = None,
        error_message: str | None = None,
    ) -> TranslationJob:
        job = TranslationJob(
            source_language=source_language,
            target_language=target_language,
            source_site=source_site,
            source_url=source_url,
            source_title=source_title,
            source_author=source_author,
            source_work_id=source_work_id,
            source_fetched_at=source_fetched_at,
            original_text=original_text,
            translated_text=translated_text,
            model_name=model_name,
            prompt_version=prompt_version,
            style=style,
            honorific_policy=honorific_policy,
            preserve_names=int(preserve_names),
            status=status,
            total_chunks=total_chunks,
            completed_chunks=completed_chunks,
            failed_chunks=failed_chunks,
            elapsed_ms=elapsed_ms,
            error_message=error_message,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_job(self, job_id: int) -> TranslationJob | None:
        return self.db.get(TranslationJob, job_id)

    def list_jobs(self, *, limit: int = 50, offset: int = 0) -> list[TranslationJob]:
        statement = (
            select(TranslationJob)
            .order_by(TranslationJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(statement))

    def update_job(
        self,
        job_id: int,
        *,
        translated_text: str | None = None,
        status: str | None = None,
        total_chunks: int | None = None,
        completed_chunks: int | None = None,
        failed_chunks: int | None = None,
        elapsed_ms: int | None = None,
        error_message: str | None = None,
    ) -> TranslationJob | None:
        job = self.get_job(job_id)
        if job is None:
            return None

        if translated_text is not None:
            job.translated_text = translated_text
        if status is not None:
            job.status = status
        if total_chunks is not None:
            job.total_chunks = total_chunks
        if completed_chunks is not None:
            job.completed_chunks = completed_chunks
        if failed_chunks is not None:
            job.failed_chunks = failed_chunks
        if elapsed_ms is not None:
            job.elapsed_ms = elapsed_ms
        if error_message is not None:
            job.error_message = error_message

        self.db.commit()
        self.db.refresh(job)
        return job
