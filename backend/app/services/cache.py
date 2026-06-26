from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import TranslationCache
from app.db.repositories.cache_repository import CacheRepository
from app.services.glossary import (
    SelectedGlossaryTerm as SelectedGlossaryTerm,
    make_selected_glossary_hash as make_selected_glossary_hash,
    make_selected_glossary_hash_for_text as make_selected_glossary_hash_for_text,
    select_glossary_terms_for_text as select_glossary_terms_for_text,
)


def make_source_text_hash(source_text: str) -> str:
    return _sha256_hex(source_text)


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


def _sha256_json(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _sha256_hex(raw)


def _sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
