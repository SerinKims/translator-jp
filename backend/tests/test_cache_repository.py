from sqlalchemy.orm import Session

from app.db.repositories.cache_repository import (
    CacheRepository,
    make_source_hash,
)


def test_save_and_find_translation_cache(db_session: Session) -> None:
    repository = CacheRepository(db_session)

    cache_entry = repository.create_cache_entry(
        source_text="source text",
        translated_text="translated text",
        glossary_hash="glossary-a",
    )

    found = repository.find_cached_translation(
        source_text="source text",
        glossary_hash="glossary-a",
    )

    assert found is not None
    assert found.id == cache_entry.id
    assert found.source_hash == cache_entry.source_hash
    assert found.source_text == "source text"
    assert found.translated_text == "translated text"
    assert found.hit_count == 0


def test_cache_lookup_uses_translation_options(db_session: Session) -> None:
    repository = CacheRepository(db_session)
    repository.create_cache_entry(
        source_text="honorific source",
        translated_text="honorific translation",
        honorific_policy="preserve",
    )

    assert (
        repository.find_cached_translation(
            source_text="honorific source",
            honorific_policy="preserve",
        )
        is not None
    )
    assert (
        repository.find_cached_translation(
            source_text="honorific source",
            honorific_policy="normalize",
        )
        is None
    )


def test_increment_cache_hit_count(db_session: Session) -> None:
    repository = CacheRepository(db_session)
    source_hash = make_source_hash(
        source_text="cache source",
        model_name="gemma4:26b-a4b-it-q4_K_M",
        prompt_version="translate_ja_ko_v1",
        style="webnovel",
        honorific_policy="preserve",
        preserve_names=True,
    )
    repository.create_cache_entry(
        source_text="cache source",
        translated_text="cache translation",
    )

    updated = repository.increment_hit_count(source_hash)

    assert updated is not None
    assert updated.hit_count == 1
