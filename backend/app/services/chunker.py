from __future__ import annotations

import re
from typing import NamedTuple, TypedDict


MAX_CHARS_PER_CHUNK = 1800
CHUNK_OVERLAP_PARAGRAPHS = 1

_BLANK_LINE_PATTERN = re.compile(r"\n[ \t]*\n+")
_OPEN_TO_CLOSE_QUOTES = {"「": "」", "『": "』"}
_CLOSE_QUOTES = set(_OPEN_TO_CLOSE_QUOTES.values())
_SENTENCE_ENDINGS = set("。！？!?")
_DIALOGUE_STARTS = tuple(_OPEN_TO_CLOSE_QUOTES)


class Chunk(TypedDict):
    index: int
    source_text: str
    context_before: str
    context_after: str


class _Unit(NamedTuple):
    text: str
    separator_before: str


def chunk_text(
    text: str,
    *,
    max_chars_per_chunk: int = MAX_CHARS_PER_CHUNK,
    overlap_paragraphs: int = CHUNK_OVERLAP_PARAGRAPHS,
) -> list[Chunk]:
    if max_chars_per_chunk <= 0:
        raise ValueError("max_chars_per_chunk must be greater than 0")
    if overlap_paragraphs < 0:
        raise ValueError("overlap_paragraphs must be greater than or equal to 0")

    normalized_text = _normalize_text(text)
    if not normalized_text:
        return []

    units = _build_units(normalized_text, max_chars_per_chunk)
    source_chunks = _pack_units(units, max_chars_per_chunk)

    chunks: list[Chunk] = []
    for index, source_text in enumerate(source_chunks):
        previous_text = source_chunks[index - 1] if index > 0 else ""
        next_text = source_chunks[index + 1] if index + 1 < len(source_chunks) else ""
        chunks.append(
            {
                "index": index,
                "source_text": source_text,
                "context_before": _context_from_text(
                    previous_text,
                    overlap_paragraphs,
                    from_end=True,
                ),
                "context_after": _context_from_text(
                    next_text,
                    overlap_paragraphs,
                    from_end=False,
                ),
            }
        )

    return chunks


def _normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def _split_paragraphs(text: str) -> list[str]:
    return [paragraph.strip() for paragraph in _BLANK_LINE_PATTERN.split(text) if paragraph.strip()]


def _build_units(text: str, max_chars: int) -> list[_Unit]:
    units: list[_Unit] = []
    for paragraph in _split_paragraphs(text):
        segments = _split_oversized_paragraph(paragraph, max_chars)
        for segment_index, segment in enumerate(segments):
            units.append(
                _Unit(
                    text=segment,
                    separator_before="\n\n" if segment_index == 0 else "",
                )
            )
    return units


def _pack_units(units: list[_Unit], max_chars: int) -> list[str]:
    chunks: list[str] = []
    current = ""

    for unit in units:
        separator = unit.separator_before if current else ""
        candidate = f"{current}{separator}{unit.text}"
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = unit.text
        else:
            hard_parts = _split_by_max_chars(unit.text, max_chars)
            chunks.extend(hard_parts[:-1])
            current = hard_parts[-1] if hard_parts else ""

        if len(current) > max_chars:
            hard_parts = _split_by_max_chars(current, max_chars)
            chunks.extend(hard_parts[:-1])
            current = hard_parts[-1] if hard_parts else ""

    if current:
        chunks.append(current)

    return chunks


def _split_oversized_paragraph(paragraph: str, max_chars: int) -> list[str]:
    if len(paragraph) <= max_chars:
        return [paragraph]

    segments: list[str] = []
    for block in _split_dialogue_blocks(paragraph):
        if len(block) <= max_chars:
            segments.append(block)
            continue
        segments.extend(_split_by_sentences(block, max_chars))
    return segments


def _split_dialogue_blocks(paragraph: str) -> list[str]:
    lines = paragraph.splitlines()
    if len(lines) <= 1:
        return [paragraph]

    blocks: list[str] = []
    current_lines: list[str] = []
    current_is_dialogue: bool | None = None
    quote_depth = 0

    for line in lines:
        stripped = line.strip()
        line_is_dialogue = quote_depth > 0 or stripped.startswith(_DIALOGUE_STARTS)

        if current_lines and (
            current_is_dialogue != line_is_dialogue
            or (current_is_dialogue and line_is_dialogue and quote_depth == 0)
        ):
            blocks.append("\n".join(current_lines).strip())
            current_lines = []

        current_lines.append(line)
        current_is_dialogue = line_is_dialogue
        quote_depth = _quote_depth_after(line, quote_depth)

    if current_lines:
        blocks.append("\n".join(current_lines).strip())

    return [block for block in blocks if block]


def _split_by_sentences(text: str, max_chars: int) -> list[str]:
    sentences = _split_sentences(text)
    segments: list[str] = []
    current = ""

    for sentence in sentences:
        candidate = f"{current}{sentence}" if current else sentence
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            segments.append(current)
            current = sentence
        else:
            hard_parts = _split_by_max_chars(sentence, max_chars)
            segments.extend(hard_parts[:-1])
            current = hard_parts[-1] if hard_parts else ""

        if len(current) > max_chars:
            hard_parts = _split_by_max_chars(current, max_chars)
            segments.extend(hard_parts[:-1])
            current = hard_parts[-1] if hard_parts else ""

    if current:
        segments.append(current)

    return segments


def _split_sentences(text: str) -> list[str]:
    sentences: list[str] = []
    quote_stack: list[str] = []
    start = 0
    last_sentence_ending = -1

    for position, char in enumerate(text):
        if char in _OPEN_TO_CLOSE_QUOTES:
            quote_stack.append(_OPEN_TO_CLOSE_QUOTES[char])
        elif quote_stack and char == quote_stack[-1]:
            quote_stack.pop()
            if not quote_stack and last_sentence_ending >= start:
                end = position + 1
                sentences.append(text[start:end])
                start = end
                last_sentence_ending = -1
            continue
        elif char in _CLOSE_QUOTES and not quote_stack:
            if last_sentence_ending >= start:
                end = position + 1
                sentences.append(text[start:end])
                start = end
                last_sentence_ending = -1
            continue

        if char in _SENTENCE_ENDINGS:
            last_sentence_ending = position
            if not quote_stack:
                end = position + 1
                sentences.append(text[start:end])
                start = end
                last_sentence_ending = -1

    tail = text[start:]
    if tail:
        sentences.append(tail)

    return [sentence for sentence in sentences if sentence]


def _quote_depth_after(text: str, initial_depth: int = 0) -> int:
    depth = initial_depth
    expected_closes: list[str] = [""] * initial_depth
    for char in text:
        if char in _OPEN_TO_CLOSE_QUOTES:
            expected_closes.append(_OPEN_TO_CLOSE_QUOTES[char])
            depth += 1
        elif expected_closes and char == expected_closes[-1]:
            expected_closes.pop()
            depth -= 1
        elif char in _CLOSE_QUOTES and depth > 0:
            depth -= 1
            if expected_closes:
                expected_closes.pop()
    return max(depth, 0)


def _split_by_max_chars(text: str, max_chars: int) -> list[str]:
    return [text[index : index + max_chars] for index in range(0, len(text), max_chars)]


def _context_from_text(text: str, overlap_paragraphs: int, *, from_end: bool) -> str:
    if not text or overlap_paragraphs == 0:
        return ""

    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        return ""

    selected = paragraphs[-overlap_paragraphs:] if from_end else paragraphs[:overlap_paragraphs]
    return "\n\n".join(selected)
