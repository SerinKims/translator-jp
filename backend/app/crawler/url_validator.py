from urllib.parse import parse_qs, urlparse


INVALID_PIXIV_URL_MESSAGE = "지원하지 않는 pixiv URL입니다. 소설 상세 페이지 URL을 입력해주세요."
PIXIV_HOST = "www.pixiv.net"
PIXIV_NOVEL_PATH = "/novel/show.php"


class UnsupportedPixivUrlError(ValueError):
    """Raised when the URL is not a supported pixiv novel detail URL."""


def validate_pixiv_novel_url(url: str) -> dict[str, str]:
    parsed_url = urlparse(url)

    if parsed_url.scheme != "https":
        raise UnsupportedPixivUrlError(INVALID_PIXIV_URL_MESSAGE)

    if parsed_url.hostname != PIXIV_HOST:
        raise UnsupportedPixivUrlError(INVALID_PIXIV_URL_MESSAGE)

    if parsed_url.path != PIXIV_NOVEL_PATH:
        raise UnsupportedPixivUrlError(INVALID_PIXIV_URL_MESSAGE)

    query = parse_qs(parsed_url.query, keep_blank_values=True)
    novel_ids = query.get("id")
    if novel_ids is None or len(novel_ids) != 1:
        raise UnsupportedPixivUrlError(INVALID_PIXIV_URL_MESSAGE)

    novel_id = novel_ids[0]
    if not novel_id.isascii() or not novel_id.isdecimal():
        raise UnsupportedPixivUrlError(INVALID_PIXIV_URL_MESSAGE)

    normalized_url = f"https://{PIXIV_HOST}{PIXIV_NOVEL_PATH}?id={novel_id}"

    return {
        "source_site": "pixiv",
        "source_url": normalized_url,
        "source_work_id": novel_id,
    }
