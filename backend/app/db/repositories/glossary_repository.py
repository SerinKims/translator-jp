from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.models import GlossarySet, GlossaryTerm


class GlossaryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
        self._ensure_sqlite_glossary_columns()

    def create_set(
        self,
        *,
        name: str,
        description: str | None = None,
        is_active: bool = True,
    ) -> GlossarySet:
        glossary_set = GlossarySet(
            name=name,
            description=description,
            is_active=int(is_active),
        )
        self.db.add(glossary_set)
        self.db.commit()
        self.db.refresh(glossary_set)
        return glossary_set

    def create_term(
        self,
        *,
        source_term: str,
        target_term: str,
        source_lang: str = "ja",
        target_lang: str = "ko",
        glossary_set_id: int | None = None,
        term_type: str = "common",
        description: str | None = None,
        aliases: list[str] | None = None,
        priority: int = 0,
        is_required: bool = True,
        is_case_sensitive: bool = False,
        is_active: bool = True,
    ) -> GlossaryTerm:
        term = GlossaryTerm(
            glossary_set_id=glossary_set_id,
            source_lang=source_lang,
            target_lang=target_lang,
            source_term=source_term,
            target_term=target_term,
            term_type=term_type,
            description=description,
            aliases=self._dump_aliases(aliases or []),
            priority=priority,
            is_required=int(is_required),
            is_case_sensitive=int(is_case_sensitive),
            is_active=int(is_active),
        )
        self.db.add(term)
        self.db.commit()
        self.db.refresh(term)
        return term

    def list_terms(
        self,
        *,
        source_lang: str | None = None,
        target_lang: str | None = None,
        active_only: bool = False,
    ) -> list[GlossaryTerm]:
        statement = select(GlossaryTerm)
        if active_only:
            statement = statement.where(GlossaryTerm.is_active == 1)
        if source_lang is not None:
            statement = statement.where(GlossaryTerm.source_lang == source_lang)
        if target_lang is not None:
            statement = statement.where(GlossaryTerm.target_lang == target_lang)
        statement = statement.order_by(
            GlossaryTerm.is_required.desc(),
            GlossaryTerm.priority.desc(),
            GlossaryTerm.source_term,
            GlossaryTerm.id,
        )
        return list(self.db.scalars(statement))

    def list_active_terms(
        self,
        *,
        source_lang: str | None = None,
        target_lang: str | None = None,
    ) -> list[GlossaryTerm]:
        return self.list_terms(
            source_lang=source_lang,
            target_lang=target_lang,
            active_only=True,
        )

    def _dump_aliases(self, aliases: list[str]) -> str:
        cleaned = [alias for alias in aliases if alias]
        return json.dumps(cleaned, ensure_ascii=False)

    def _ensure_sqlite_glossary_columns(self) -> None:
        bind = self.db.get_bind()
        if bind.dialect.name != "sqlite":
            return

        rows = self.db.execute(text("PRAGMA table_info(glossary_terms)")).mappings().all()
        if not rows:
            return

        existing_columns = {str(row["name"]) for row in rows}
        migrations = {
            "source_lang": "ALTER TABLE glossary_terms ADD COLUMN source_lang TEXT NOT NULL DEFAULT 'ja'",
            "target_lang": "ALTER TABLE glossary_terms ADD COLUMN target_lang TEXT NOT NULL DEFAULT 'ko'",
            "aliases": "ALTER TABLE glossary_terms ADD COLUMN aliases TEXT",
            "priority": "ALTER TABLE glossary_terms ADD COLUMN priority INTEGER NOT NULL DEFAULT 0",
            "is_required": "ALTER TABLE glossary_terms ADD COLUMN is_required INTEGER NOT NULL DEFAULT 1",
        }
        changed = False
        for column_name, statement in migrations.items():
            if column_name in existing_columns:
                continue
            self.db.execute(text(statement))
            changed = True
        if changed:
            self.db.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_glossary_terms_lang "
                    "ON glossary_terms(source_lang, target_lang)"
                )
            )
            self.db.commit()


def parse_aliases(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if not isinstance(value, str):
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if str(item)]
