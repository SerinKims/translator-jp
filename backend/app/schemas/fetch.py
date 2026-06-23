from pydantic import BaseModel, ConfigDict


class PixivFetchRequest(BaseModel):
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
