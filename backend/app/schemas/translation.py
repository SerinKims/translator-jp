from __future__ import annotations

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
