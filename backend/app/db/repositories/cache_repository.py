from __future__ import annotations

import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import TranslationCache


def make_source_hash(
    *,
    source_text: str,
    model_name: str,
    prompt_version: str,
    style: str,
    honorific_policy: str,
    preserve_names: bool,
    glossary_hash: str | None = None,
) -> str:
    raw = "|".join(
        [
            source_text,
            model_name,
            prompt_version,
            style,
            honorific_policy,
            str(preserve_names),
            glossary_hash or "",
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class CacheRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_cache_entry(
        self,
        *,
        source_text: str,
        translated_text: str,
        model_name: str = "gemma4-e4b",
        prompt_version: str = "translate_ja_ko_v1",
        style: str = "webnovel",
        honorific_policy: str = "preserve",
        preserve_names: bool = True,
        glossary_hash: str | None = None,
        hit_count: int = 0,
    ) -> TranslationCache:
        source_hash = make_source_hash(
            source_text=source_text,
            model_name=model_name,
            prompt_version=prompt_version,
            style=style,
            honorific_policy=honorific_policy,
            preserve_names=preserve_names,
            glossary_hash=glossary_hash,
        )
        cache_entry = TranslationCache(
            source_hash=source_hash,
            source_text=source_text,
            translated_text=translated_text,
            model_name=model_name,
            prompt_version=prompt_version,
            style=style,
            honorific_policy=honorific_policy,
            preserve_names=int(preserve_names),
            glossary_hash=glossary_hash,
            hit_count=hit_count,
        )
        self.db.add(cache_entry)
        self.db.commit()
        self.db.refresh(cache_entry)
        return cache_entry

    def get_by_source_hash(self, source_hash: str) -> TranslationCache | None:
        return self.db.scalar(
            select(TranslationCache).where(TranslationCache.source_hash == source_hash)
        )

    def find_cached_translation(
        self,
        *,
        source_text: str,
        model_name: str = "gemma4-e4b",
        prompt_version: str = "translate_ja_ko_v1",
        style: str = "webnovel",
        honorific_policy: str = "preserve",
        preserve_names: bool = True,
        glossary_hash: str | None = None,
    ) -> TranslationCache | None:
        source_hash = make_source_hash(
            source_text=source_text,
            model_name=model_name,
            prompt_version=prompt_version,
            style=style,
            honorific_policy=honorific_policy,
            preserve_names=preserve_names,
            glossary_hash=glossary_hash,
        )
        return self.get_by_source_hash(source_hash)

    def increment_hit_count(self, source_hash: str) -> TranslationCache | None:
        cache_entry = self.get_by_source_hash(source_hash)
        if cache_entry is None:
            return None

        cache_entry.hit_count += 1
        self.db.commit()
        self.db.refresh(cache_entry)
        return cache_entry
