from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.models import TranslationCache


class CacheRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
        self._ensure_sqlite_language_columns()

    def create_cache_entry(
        self,
        *,
        cache_key: str,
        source_text: str,
        translated_text: str,
        source_lang: str = "ja",
        target_lang: str = "ko",
        model_name: str = "gemma4:26b-a4b-it-q4_K_M",
        prompt_version: str = "translate_ja_ko_v1",
        style: str = "webnovel",
        honorific_policy: str = "preserve",
        preserve_names: bool = True,
        selected_glossary_hash: str | None = None,
        hit_count: int = 0,
    ) -> TranslationCache:
        cache_entry = TranslationCache(
            source_hash=cache_key,
            source_lang=source_lang,
            target_lang=target_lang,
            source_text=source_text,
            translated_text=translated_text,
            model_name=model_name,
            prompt_version=prompt_version,
            style=style,
            honorific_policy=honorific_policy,
            preserve_names=int(preserve_names),
            glossary_hash=selected_glossary_hash,
            hit_count=hit_count,
        )
        self.db.add(cache_entry)
        self.db.commit()
        self.db.refresh(cache_entry)
        return cache_entry

    def get_by_cache_key(self, cache_key: str) -> TranslationCache | None:
        return self.get_by_source_hash(cache_key)

    def get_by_source_hash(self, source_hash: str) -> TranslationCache | None:
        return self.db.scalar(
            select(TranslationCache).where(TranslationCache.source_hash == source_hash)
        )

    def increment_hit_count(self, source_hash: str) -> TranslationCache | None:
        cache_entry = self.get_by_source_hash(source_hash)
        if cache_entry is None:
            return None

        cache_entry.hit_count += 1
        self.db.commit()
        self.db.refresh(cache_entry)
        return cache_entry

    def _ensure_sqlite_language_columns(self) -> None:
        bind = self.db.get_bind()
        if bind.dialect.name != "sqlite":
            return

        rows = self.db.execute(text("PRAGMA table_info(translation_cache)")).mappings().all()
        if not rows:
            self.db.commit()
            return

        existing_columns = {str(row["name"]) for row in rows}
        migrations = {
            "source_lang": (
                "ALTER TABLE translation_cache ADD COLUMN source_lang TEXT NOT NULL DEFAULT 'ja'"
            ),
            "target_lang": (
                "ALTER TABLE translation_cache ADD COLUMN target_lang TEXT NOT NULL DEFAULT 'ko'"
            ),
        }
        changed = False
        for column_name, statement in migrations.items():
            if column_name in existing_columns:
                continue
            self.db.execute(text(statement))
            changed = True
        if changed:
            self.db.commit()
