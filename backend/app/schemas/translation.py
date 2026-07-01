from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, field_validator


class OllamaRequestOptions(BaseModel):
    think: str | bool = False
    options: dict[str, Any] | None = None

    @field_validator("think", mode="before")
    @classmethod
    def validate_think(cls, value: Any) -> Any:
        if isinstance(value, bool) or isinstance(value, str):
            return value
        raise ValueError("think must be a string or boolean")


class TranslationRequest(OllamaRequestOptions):
    text: str
    source_lang: str = "ja"
    target_lang: str = "ko"
    translate_scope: Literal["first_page", "current_page", "all_pages"] = "first_page"
    page_index: int = 0
    style: str = "webnovel"
    honorific_policy: str = "preserve"
    preserve_names: bool = True
    use_glossary: bool = True
    use_cache: bool = True
    stream: bool = False


class PageTranslateRequest(OllamaRequestOptions):
    source_lang: str = "ja"
    target_lang: str = "ko"
    translate_scope: Literal["current_page"] = "current_page"
    style: str = "webnovel"
    honorific_policy: str = "preserve"
    preserve_names: bool = True
    use_glossary: bool = True
    use_cache: bool = True
    stream: bool = False
    force: bool = False


class TranslationChunkResponse(BaseModel):
    index: int
    source_lang: str
    target_lang: str
    status: str


class TranslationResponse(BaseModel):
    job_id: int
    source_type: str = "pasted_text"
    source_lang: str
    target_lang: str
    current_page_index: int
    total_pages: int
    has_next_page: bool
    translated_text: str
    model: str
    prompt_version: str
    style: str
    elapsed_ms: int
    cache_hit: bool
    chunks: list[TranslationChunkResponse]


class TranslationHistoryItem(BaseModel):
    job_id: int
    source_site: str
    source_url: str | None
    source_title: str | None
    source_author: str | None
    source_work_id: str | None
    source_fetched_at: datetime | None
    source_preview: str
    translated_preview: str | None
    source_lang: str
    target_lang: str
    model_name: str
    prompt_version: str
    ollama_think: str | None
    ollama_options_json: str | None
    style: str
    honorific_policy: str
    preserve_names: bool
    status: str
    total_pages: int
    total_chunks: int
    completed_chunks: int
    failed_chunks: int
    elapsed_ms: int | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class TranslationPageHistory(BaseModel):
    id: int
    page_index: int
    page_title: str | None
    source_text: str
    translated_text: str | None
    status: str
    total_chunks: int
    completed_chunks: int
    failed_chunks: int
    elapsed_ms: int | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class TranslationChunkHistory(BaseModel):
    id: int
    page_id: int
    page_index: int | None
    chunk_index: int
    source_lang: str
    target_lang: str
    source_text: str
    translated_text: str | None
    context_before: str | None
    context_after: str | None
    status: str
    retry_count: int
    prompt_used: str | None
    raw_model_response: str | None
    elapsed_ms: int | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class TranslationDetailResponse(TranslationHistoryItem):
    original_text: str
    translated_text: str | None
    pages: list[TranslationPageHistory]
    chunks: list[TranslationChunkHistory]
