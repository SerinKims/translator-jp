from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable

from sqlalchemy.orm import Session

from app.db.models import TranslationCache
from app.db.repositories.cache_repository import CacheRepository


@dataclass(frozen=True)
class SelectedGlossaryTerm:
    source_term: str
    target_term: str
    term_type: str
    description: str | None
    is_case_sensitive: bool


def make_source_text_hash(source_text: str) -> str:
    return _sha256_hex(source_text)


def select_glossary_terms_for_text(
    source_text: str,
    glossary_terms: Iterable[Any],
) -> list[SelectedGlossaryTerm]:
    selected: list[SelectedGlossaryTerm] = []
    for term in glossary_terms:
        selected_term = _to_selected_term(term)
        if not selected_term.source_term:
            continue
        haystack = source_text if selected_term.is_case_sensitive else source_text.lower()
        needle = (
            selected_term.source_term
            if selected_term.is_case_sensitive
            else selected_term.source_term.lower()
        )
        if needle in haystack:
            selected.append(selected_term)

    return sorted(
        selected,
        key=lambda item: (
            item.source_term,
            item.target_term,
            item.term_type,
            item.description or "",
            item.is_case_sensitive,
        ),
    )


def make_selected_glossary_hash(selected_terms: Iterable[Any]) -> str:
    normalized = [_term_to_cache_dict(_to_selected_term(term)) for term in selected_terms]
    normalized.sort(
        key=lambda item: (
            item["source_term"],
            item["target_term"],
            item["term_type"],
            item["description"] or "",
            item["is_case_sensitive"],
        )
    )
    return _sha256_json(normalized)


def make_selected_glossary_hash_for_text(
    source_text: str,
    glossary_terms: Iterable[Any],
) -> str:
    selected_terms = select_glossary_terms_for_text(source_text, glossary_terms)
    return make_selected_glossary_hash(selected_terms)


def make_cache_key(
    *,
    source_text_hash: str,
    source_lang: str,
    target_lang: str,
    model_name: str,
    prompt_version: str,
    style: str,
    honorific_policy: str,
    preserve_names: bool,
    selected_glossary_hash: str,
) -> str:
    return _sha256_json(
        {
            "source_text_hash": source_text_hash,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "model_name": model_name,
            "prompt_version": prompt_version,
            "style": style,
            "honorific_policy": honorific_policy,
            "preserve_names": preserve_names,
            "selected_glossary_hash": selected_glossary_hash,
        }
    )


def build_cache_key(
    *,
    source_text: str,
    source_lang: str,
    target_lang: str,
    model_name: str,
    prompt_version: str,
    style: str,
    honorific_policy: str,
    preserve_names: bool,
    selected_glossary_hash: str,
) -> str:
    return make_cache_key(
        source_text_hash=make_source_text_hash(source_text),
        source_lang=source_lang,
        target_lang=target_lang,
        model_name=model_name,
        prompt_version=prompt_version,
        style=style,
        honorific_policy=honorific_policy,
        preserve_names=preserve_names,
        selected_glossary_hash=selected_glossary_hash,
    )


class TranslationCacheService:
    def __init__(self, db: Session) -> None:
        self.repository = CacheRepository(db)

    def get_cached_translation(
        self,
        *,
        cache_key: str,
    ) -> TranslationCache | None:
        cache_entry = self.repository.get_by_cache_key(cache_key)
        if cache_entry is None:
            return None
        return self.repository.increment_hit_count(cache_key)

    def save_translation(
        self,
        *,
        cache_key: str,
        source_text: str,
        translated_text: str,
        model_name: str,
        prompt_version: str,
        style: str,
        honorific_policy: str,
        preserve_names: bool,
        selected_glossary_hash: str,
    ) -> TranslationCache:
        return self.repository.create_cache_entry(
            cache_key=cache_key,
            source_text=source_text,
            translated_text=translated_text,
            model_name=model_name,
            prompt_version=prompt_version,
            style=style,
            honorific_policy=honorific_policy,
            preserve_names=preserve_names,
            selected_glossary_hash=selected_glossary_hash,
        )


def _to_selected_term(term: Any) -> SelectedGlossaryTerm:
    if isinstance(term, SelectedGlossaryTerm):
        return term
    return SelectedGlossaryTerm(
        source_term=str(_get_term_value(term, "source_term", "") or ""),
        target_term=str(_get_term_value(term, "target_term", "") or ""),
        term_type=str(_get_term_value(term, "term_type", "common") or "common"),
        description=_get_optional_str(term, "description"),
        is_case_sensitive=bool(_get_term_value(term, "is_case_sensitive", False)),
    )


def _get_term_value(term: Any, name: str, default: Any) -> Any:
    if isinstance(term, dict):
        return term.get(name, default)
    return getattr(term, name, default)


def _get_optional_str(term: Any, name: str) -> str | None:
    value = _get_term_value(term, name, None)
    if value is None:
        return None
    return str(value)


def _term_to_cache_dict(term: SelectedGlossaryTerm) -> dict[str, Any]:
    return {
        "source_term": term.source_term,
        "target_term": term.target_term,
        "term_type": term.term_type,
        "description": term.description,
        "is_case_sensitive": term.is_case_sensitive,
    }


def _sha256_json(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _sha256_hex(raw)


def _sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
