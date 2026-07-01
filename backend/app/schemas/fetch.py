from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.translation import OllamaRequestOptions, TranslationChunkResponse


class PixivFetchRequest(OllamaRequestOptions):
    url: str
    translate_after_fetch: bool = False


class PixivTranslateRequest(OllamaRequestOptions):
    url: str
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


class PixivFetchResponse(BaseModel):
    source_site: str
    source_url: str
    source_work_id: str
    title: str
    author: str
    text: str
    char_count: int
    job_id: int

    model_config = ConfigDict(from_attributes=True)


class PixivTranslateResponse(BaseModel):
    job_id: int
    source_site: str
    source_url: str
    source_work_id: str
    title: str
    author: str
    current_page_index: int
    total_pages: int
    has_next_page: bool
    translated_text: str
    model: str
    prompt_version: str
    elapsed_ms: int
    chunks: list[TranslationChunkResponse]

    model_config = ConfigDict(from_attributes=True)
