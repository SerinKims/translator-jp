from __future__ import annotations

from dataclasses import dataclass


PIXIV_FETCH_FAILED_MESSAGE = (
    "pixiv 원문을 가져오지 못했습니다. URL을 확인하거나 원문을 직접 입력해주세요."
)
PIXIV_ACCESS_DENIED_MESSAGE = (
    "해당 pixiv 페이지에 접근할 수 없습니다. 브라우저에서 열람 가능한 페이지인지 확인해주세요."
)
PIXIV_PARSE_FAILED_MESSAGE = (
    "페이지는 열렸지만 소설 원문을 찾지 못했습니다. 원문을 직접 입력해주세요."
)


@dataclass(frozen=True)
class PixivFetchedPage:
    url: str
    html: str
    status_code: int


@dataclass(frozen=True)
class PixivNovel:
    source_site: str
    source_url: str
    source_work_id: str
    title: str
    author: str
    text: str
    char_count: int
