from pydantic import BaseModel, ConfigDict

from app.schemas.translation import OllamaRequestOptions


class PixivFetchRequest(OllamaRequestOptions):
    url: str
    translate_after_fetch: bool = False


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
