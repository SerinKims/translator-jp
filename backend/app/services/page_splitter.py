from __future__ import annotations

from dataclasses import dataclass

NEWPAGE_MARKER = "[newpage]"


@dataclass(frozen=True)
class SourcePage:
    page_index: int
    source_text: str
    page_title: str | None = None


def has_newpage_marker(source_text: str) -> bool:
    return NEWPAGE_MARKER in source_text


def split_pages(source_text: str) -> list[SourcePage]:
    raw_pages = (
        source_text.split(NEWPAGE_MARKER) if has_newpage_marker(source_text) else [source_text]
    )
    pages = [
        SourcePage(page_index=index, source_text=text.strip())
        for index, text in enumerate(text for text in raw_pages if text.strip())
    ]
    if pages:
        return pages
    return [SourcePage(page_index=0, source_text="")]
