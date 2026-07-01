from sqlalchemy.orm import Session

from app.db.repositories.cache_repository import CacheRepository


def test_save_and_find_translation_cache_by_cache_key(db_session: Session) -> None:
    repository = CacheRepository(db_session)

    cache_entry = repository.create_cache_entry(
        cache_key="cache-key-a",
        source_text="source text",
        translated_text="translated text",
        selected_glossary_hash="selected-glossary-a",
    )

    found = repository.get_by_cache_key("cache-key-a")

    assert found is not None
    assert found.id == cache_entry.id
    assert found.source_hash == "cache-key-a"
    assert found.source_lang == "ja"
    assert found.target_lang == "ko"
    assert found.glossary_hash == "selected-glossary-a"
    assert found.source_text == "source text"
    assert found.translated_text == "translated text"
    assert found.hit_count == 0


def test_same_cache_key_lookup_succeeds(db_session: Session) -> None:
    repository = CacheRepository(db_session)
    repository.create_cache_entry(
        cache_key="same-cache-key",
        source_text="source text",
        translated_text="translated text",
    )

    assert repository.get_by_cache_key("same-cache-key") is not None


def test_different_cache_key_lookup_fails(db_session: Session) -> None:
    repository = CacheRepository(db_session)
    repository.create_cache_entry(
        cache_key="cache-key-a",
        source_text="source text",
        translated_text="translated text",
    )

    assert repository.get_by_cache_key("cache-key-b") is None


def test_increment_cache_hit_count(db_session: Session) -> None:
    repository = CacheRepository(db_session)
    repository.create_cache_entry(
        cache_key="cache-key-a",
        source_text="cache source",
        translated_text="cache translation",
    )

    updated = repository.increment_hit_count("cache-key-a")

    assert updated is not None
    assert updated.hit_count == 1


def test_increment_missing_cache_key_is_safe(db_session: Session) -> None:
    repository = CacheRepository(db_session)

    assert repository.increment_hit_count("missing-cache-key") is None


def test_save_translation_cache_with_language_pair(db_session: Session) -> None:
    repository = CacheRepository(db_session)

    cache_entry = repository.create_cache_entry(
        cache_key="cache-key-en",
        source_text="source text",
        translated_text="translated text",
        source_lang="en",
        target_lang="ko",
    )

    assert cache_entry.source_lang == "en"
    assert cache_entry.target_lang == "ko"
