import pytest

from app.crawler.url_validator import (
    INVALID_PIXIV_URL_MESSAGE,
    UnsupportedPixivUrlError,
    validate_pixiv_novel_url,
)


def test_valid_pixiv_novel_url_passes() -> None:
    result = validate_pixiv_novel_url("https://www.pixiv.net/novel/show.php?id=12345678")

    assert result == {
        "source_site": "pixiv",
        "source_url": "https://www.pixiv.net/novel/show.php?id=12345678",
        "source_work_id": "12345678",
    }


def test_extracts_novel_id() -> None:
    result = validate_pixiv_novel_url("https://www.pixiv.net/novel/show.php?id=87654321")

    assert result["source_work_id"] == "87654321"


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/novel/show.php?id=12345678",
        "https://pixiv.net/novel/show.php?id=12345678",
    ],
)
def test_rejects_non_pixiv_or_unsupported_domain(url: str) -> None:
    with pytest.raises(UnsupportedPixivUrlError, match=INVALID_PIXIV_URL_MESSAGE):
        validate_pixiv_novel_url(url)


def test_rejects_series_url() -> None:
    with pytest.raises(UnsupportedPixivUrlError, match=INVALID_PIXIV_URL_MESSAGE):
        validate_pixiv_novel_url("https://www.pixiv.net/novel/series/1234567")


def test_rejects_url_without_id() -> None:
    with pytest.raises(UnsupportedPixivUrlError, match=INVALID_PIXIV_URL_MESSAGE):
        validate_pixiv_novel_url("https://www.pixiv.net/novel/show.php")


def test_rejects_non_numeric_id() -> None:
    with pytest.raises(UnsupportedPixivUrlError, match=INVALID_PIXIV_URL_MESSAGE):
        validate_pixiv_novel_url("https://www.pixiv.net/novel/show.php?id=not-a-number")


def test_normalizes_url() -> None:
    result = validate_pixiv_novel_url(
        "https://www.pixiv.net/novel/show.php?utm_source=test&id=12345678"
    )

    assert result["source_url"] == "https://www.pixiv.net/novel/show.php?id=12345678"
