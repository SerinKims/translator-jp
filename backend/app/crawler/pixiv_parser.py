from __future__ import annotations

import html as html_lib
import json
import re
from collections.abc import Iterable
from typing import Any

from bs4 import BeautifulSoup, Tag

from app.crawler.pixiv_types import PIXIV_PARSE_FAILED_MESSAGE, PixivNovel
from app.crawler.url_validator import validate_pixiv_novel_url


class PixivParseError(ValueError):
    def __init__(self, message: str = PIXIV_PARSE_FAILED_MESSAGE) -> None:
        super().__init__(message)
        self.message = message


def parse_pixiv_novel_html(html: str, source_url: str) -> PixivNovel:
    source = validate_pixiv_novel_url(source_url)
    source_work_id = source["source_work_id"]

    json_data = _extract_json_document(html)
    if json_data is not None:
        novel = _extract_novel_from_next_data(json_data, source_work_id)
        if novel is not None:
            return _build_novel(source["source_url"], source_work_id, novel)

    soup = BeautifulSoup(html, "html.parser")

    preload_data = _extract_meta_preload_data(soup)
    if preload_data is not None:
        novel = _extract_novel_from_preload(preload_data, source_work_id)
        if novel is not None:
            return _build_novel(source["source_url"], source_work_id, novel)

    next_data = _extract_next_data(soup)
    if next_data is not None:
        novel = _extract_novel_from_next_data(next_data, source_work_id)
        if novel is not None:
            return _build_novel(source["source_url"], source_work_id, novel)

    fallback = _extract_from_html(soup)
    return _build_novel(source["source_url"], source_work_id, fallback)


def _build_novel(source_url: str, source_work_id: str, raw: dict[str, Any]) -> PixivNovel:
    title = _clean_single_line(str(raw.get("title") or ""))
    author = _clean_single_line(str(raw.get("author") or raw.get("userName") or ""))
    text = _clean_text(str(raw.get("text") or raw.get("content") or ""))

    if not text:
        raise PixivParseError()

    return PixivNovel(
        source_site="pixiv",
        source_url=source_url,
        source_work_id=source_work_id,
        title=title,
        author=author,
        text=text,
        char_count=len(text),
    )


def _extract_meta_preload_data(soup: BeautifulSoup) -> dict[str, Any] | None:
    preload = soup.find("meta", id="meta-preload-data")
    if not isinstance(preload, Tag):
        return None

    content = preload.get("content")
    if not isinstance(content, str) or not content.strip():
        return None

    try:
        payload = json.loads(html_lib.unescape(content))
    except json.JSONDecodeError:
        return None

    return payload if isinstance(payload, dict) else None


def _extract_novel_from_preload(
    payload: dict[str, Any],
    source_work_id: str,
) -> dict[str, Any] | None:
    novels = payload.get("novel")
    if not isinstance(novels, dict):
        return None

    raw = novels.get(source_work_id)
    if not isinstance(raw, dict):
        return None

    return {
        "title": raw.get("title"),
        "author": raw.get("userName") or _nested_get(raw, ("authorDetails", "userName")),
        "content": raw.get("content"),
    }


def _extract_next_data(soup: BeautifulSoup) -> dict[str, Any] | None:
    script = soup.find("script", id="__NEXT_DATA__")
    if not isinstance(script, Tag) or script.string is None:
        return None

    try:
        payload = json.loads(script.string)
    except json.JSONDecodeError:
        return None

    return payload if isinstance(payload, dict) else None


def _extract_json_document(document: str) -> dict[str, Any] | None:
    stripped = document.strip()
    if not stripped.startswith("{"):
        return None

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return None

    return payload if isinstance(payload, dict) else None


def _extract_novel_from_next_data(
    payload: dict[str, Any],
    source_work_id: str,
) -> dict[str, Any] | None:
    for value in _walk_values(payload):
        if not isinstance(value, dict):
            continue
        if str(value.get("id") or value.get("novelId") or "") != source_work_id:
            continue
        content = value.get("content") or value.get("text")
        if not isinstance(content, str):
            continue
        return {
            "title": value.get("title"),
            "author": value.get("userName") or value.get("authorName"),
            "content": content,
        }
    return None


def _extract_from_html(soup: BeautifulSoup) -> dict[str, str]:
    for tag in soup(["script", "style", "noscript", "nav", "header", "footer"]):
        tag.decompose()

    title = _first_text(
        soup,
        [
            '[data-testid="novel-title"]',
            "h1",
        ],
    )
    if not title:
        title = _meta_content(soup, "property", "og:title")
        title = re.sub(r"\s*-\s*pixiv\s*$", "", title, flags=re.IGNORECASE)

    author = _first_text(
        soup,
        [
            '[data-testid="user-name"]',
            'a[href^="/users/"]',
            'a[href*="/users/"]',
        ],
    )
    if not author:
        author = _meta_content(soup, "name", "author")

    content_node = _first_node(
        soup,
        [
            '[data-testid="novel-content"]',
            "article",
            ".novel-content",
            "#novel-content",
        ],
    )
    text = ""
    if content_node is not None:
        for tag in content_node(["script", "style", "button", "nav", "header", "footer"]):
            tag.decompose()
        text = content_node.get_text("\n", strip=True)

    return {
        "title": title,
        "author": author,
        "text": text,
    }


def _first_node(soup: BeautifulSoup, selectors: Iterable[str]) -> Tag | None:
    for selector in selectors:
        node = soup.select_one(selector)
        if isinstance(node, Tag):
            return node
    return None


def _first_text(soup: BeautifulSoup, selectors: Iterable[str]) -> str:
    node = _first_node(soup, selectors)
    if node is None:
        return ""
    return _clean_single_line(node.get_text(" "))


def _meta_content(soup: BeautifulSoup, attr: str, value: str) -> str:
    node = soup.find("meta", attrs={attr: value})
    if not isinstance(node, Tag):
        return ""
    content = node.get("content")
    return _clean_single_line(content if isinstance(content, str) else "")


def _clean_text(value: str) -> str:
    text = html_lib.unescape(value).replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _clean_single_line(value: str) -> str:
    return re.sub(r"\s+", " ", html_lib.unescape(value)).strip()


def _nested_get(data: dict[str, Any], keys: tuple[str, ...]) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _walk_values(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for nested in value.values():
            yield from _walk_values(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_values(nested)
    elif isinstance(value, str):
        stripped = value.strip()
        if not stripped.startswith(("{", "[")):
            return
        try:
            nested_json = json.loads(stripped)
        except json.JSONDecodeError:
            return
        yield from _walk_values(nested_json)
