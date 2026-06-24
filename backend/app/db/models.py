from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )


class TranslationJob(TimestampMixin, Base):
    __tablename__ = "translation_jobs"
    __table_args__ = (
        CheckConstraint(
            "source_site IN ('manual', 'pixiv')", name="ck_translation_jobs_source_site"
        ),
        CheckConstraint(
            "status IN ("
            "'pending', 'fetched', 'pending_translation', "
            "'running', 'completed', 'failed', 'cancelled'"
            ")",
            name="ck_translation_jobs_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_language: Mapped[str] = mapped_column(String, nullable=False, default="ja")
    target_language: Mapped[str] = mapped_column(String, nullable=False, default="ko")

    source_site: Mapped[str] = mapped_column(String, nullable=False, default="manual")
    source_url: Mapped[str | None] = mapped_column(Text)
    source_title: Mapped[str | None] = mapped_column(Text)
    source_author: Mapped[str | None] = mapped_column(Text)
    source_work_id: Mapped[str | None] = mapped_column(String)
    source_fetched_at: Mapped[datetime | None] = mapped_column(DateTime)

    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    translated_text: Mapped[str | None] = mapped_column(Text)

    model_name: Mapped[str] = mapped_column(String, nullable=False, default="gemma4-e4b")
    prompt_version: Mapped[str] = mapped_column(String, nullable=False, default="translate_ja_ko_v1")
    style: Mapped[str] = mapped_column(String, nullable=False, default="webnovel")
    honorific_policy: Mapped[str] = mapped_column(String, nullable=False, default="preserve")
    preserve_names: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    total_chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    elapsed_ms: Mapped[int | None] = mapped_column(Integer)

    chunks: Mapped[list[TranslationChunk]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )


class TranslationChunk(TimestampMixin, Base):
    __tablename__ = "translation_chunks"
    __table_args__ = (
        UniqueConstraint("job_id", "chunk_index", name="uq_translation_chunks_job_index"),
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'skipped')",
            name="ck_translation_chunks_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("translation_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    translated_text: Mapped[str | None] = mapped_column(Text)
    context_before: Mapped[str | None] = mapped_column(Text)
    context_after: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    prompt_used: Mapped[str | None] = mapped_column(Text)
    raw_model_response: Mapped[str | None] = mapped_column(Text)
    elapsed_ms: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)

    job: Mapped[TranslationJob] = relationship(back_populates="chunks")


class GlossarySet(TimestampMixin, Base):
    __tablename__ = "glossary_sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    terms: Mapped[list[GlossaryTerm]] = relationship(
        back_populates="glossary_set",
        cascade="all, delete-orphan",
    )


class GlossaryTerm(TimestampMixin, Base):
    __tablename__ = "glossary_terms"
    __table_args__ = (
        UniqueConstraint("glossary_set_id", "source_term", name="uq_glossary_terms_set_source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    glossary_set_id: Mapped[int | None] = mapped_column(
        ForeignKey("glossary_sets.id", ondelete="CASCADE"),
    )
    source_term: Mapped[str] = mapped_column(String, nullable=False)
    target_term: Mapped[str] = mapped_column(String, nullable=False)
    term_type: Mapped[str] = mapped_column(String, nullable=False, default="common")
    description: Mapped[str | None] = mapped_column(Text)
    is_case_sensitive: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    glossary_set: Mapped[GlossarySet | None] = relationship(back_populates="terms")


class TranslationCache(TimestampMixin, Base):
    __tablename__ = "translation_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_hash: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    translated_text: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String, nullable=False)
    style: Mapped[str] = mapped_column(String, nullable=False)
    honorific_policy: Mapped[str] = mapped_column(String, nullable=False, default="preserve")
    preserve_names: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    glossary_hash: Mapped[str | None] = mapped_column(String)
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class TranslationFeedback(Base):
    __tablename__ = "translation_feedback"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_translation_feedback_rating"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int | None] = mapped_column(
        ForeignKey("translation_jobs.id", ondelete="SET NULL")
    )
    chunk_id: Mapped[int | None] = mapped_column(
        ForeignKey("translation_chunks.id", ondelete="SET NULL"),
    )
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    model_translation: Mapped[str] = mapped_column(Text, nullable=False)
    user_corrected_translation: Mapped[str | None] = mapped_column(Text)
    rating: Mapped[int | None] = mapped_column(Integer)
    feedback_type: Mapped[str | None] = mapped_column(String)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    task_type: Mapped[str] = mapped_column(String, nullable=False, default="translation")
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    user_prompt_template: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_name: Mapped[str | None] = mapped_column(String)
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String, nullable=False)
    dataset_name: Mapped[str] = mapped_column(String, nullable=False)
    total_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    passed_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_elapsed_ms: Mapped[int | None] = mapped_column(Integer)
    no_japanese_left_score: Mapped[float | None] = mapped_column(Float)
    paragraph_match_score: Mapped[float | None] = mapped_column(Float)
    glossary_preserve_score: Mapped[float | None] = mapped_column(Float)
    dialogue_style_score: Mapped[float | None] = mapped_column(Float)
    no_empty_translation_score: Mapped[float | None] = mapped_column(Float)
    report_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )

    results: Mapped[list[EvalResult]] = relationship(
        back_populates="eval_run",
        cascade="all, delete-orphan",
    )


class EvalResult(Base):
    __tablename__ = "eval_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    eval_run_id: Mapped[int] = mapped_column(
        ForeignKey("eval_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[str] = mapped_column(String, nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_translation: Mapped[str | None] = mapped_column(Text)
    actual_translation: Mapped[str | None] = mapped_column(Text)
    passed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score: Mapped[float | None] = mapped_column(Float)
    fail_reason: Mapped[str | None] = mapped_column(Text)
    elapsed_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )

    eval_run: Mapped[EvalRun] = relationship(back_populates="results")


class UserSettings(TimestampMixin, Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    default_style: Mapped[str] = mapped_column(String, nullable=False, default="webnovel")
    default_honorific_policy: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="preserve",
    )
    default_preserve_names: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    default_model_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="gemma4-e4b",
    )
    default_prompt_version: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="translate_ja_ko_v1",
    )
    auto_use_glossary: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    auto_cache_enabled: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
