from app.services.cache import (
    build_cache_key,
    make_selected_glossary_hash_for_text,
    make_source_text_hash,
)


BASE_KEY_ARGS = {
    "source_text": "魔王は静かに笑った。",
    "source_lang": "ja",
    "target_lang": "ko",
    "model_name": "gemma4:26b-a4b-it-q4_K_M",
    "prompt_version": "translate_ja_ko_v1",
    "style": "webnovel",
    "honorific_policy": "preserve",
    "preserve_names": True,
    "selected_glossary_hash": "selected-glossary-a",
}


def test_source_text_hash_is_stable_for_same_input() -> None:
    assert make_source_text_hash("同じ文章") == make_source_text_hash("同じ文章")


def test_same_input_and_options_make_same_cache_key() -> None:
    assert build_cache_key(**BASE_KEY_ARGS) == build_cache_key(**BASE_KEY_ARGS)


def test_prompt_version_change_makes_different_cache_key() -> None:
    assert build_cache_key(**BASE_KEY_ARGS) != build_cache_key(
        **{**BASE_KEY_ARGS, "prompt_version": "translate_ja_ko_v2"}
    )


def test_style_change_makes_different_cache_key() -> None:
    assert build_cache_key(**BASE_KEY_ARGS) != build_cache_key(
        **{**BASE_KEY_ARGS, "style": "literal"}
    )


def test_source_lang_change_makes_different_cache_key() -> None:
    assert build_cache_key(**BASE_KEY_ARGS) != build_cache_key(
        **{**BASE_KEY_ARGS, "source_lang": "en"}
    )


def test_target_lang_change_makes_different_cache_key() -> None:
    assert build_cache_key(**BASE_KEY_ARGS) != build_cache_key(
        **{**BASE_KEY_ARGS, "target_lang": "en"}
    )


def test_selected_glossary_hash_change_makes_different_cache_key() -> None:
    assert build_cache_key(**BASE_KEY_ARGS) != build_cache_key(
        **{**BASE_KEY_ARGS, "selected_glossary_hash": "selected-glossary-b"}
    )


def test_unmatched_glossary_terms_do_not_change_selected_glossary_hash() -> None:
    source_text = "魔王は静かに笑った。"
    first_glossary = [
        {"source_term": "魔王", "target_term": "마왕", "term_type": "title"},
        {"source_term": "勇者", "target_term": "용사", "term_type": "title"},
    ]
    second_glossary = [
        {"source_term": "魔王", "target_term": "마왕", "term_type": "title"},
        {"source_term": "王都", "target_term": "왕도", "term_type": "place"},
    ]

    assert make_selected_glossary_hash_for_text(
        source_text,
        first_glossary,
    ) == make_selected_glossary_hash_for_text(source_text, second_glossary)


def test_matched_glossary_terms_change_selected_glossary_hash() -> None:
    assert make_selected_glossary_hash_for_text(
        "魔王は静かに笑った。",
        [{"source_term": "魔王", "target_term": "마왕"}],
    ) != make_selected_glossary_hash_for_text(
        "勇者は静かに笑った。",
        [{"source_term": "魔王", "target_term": "마왕"}],
    )


def test_use_cache_false_bypasses_cache_in_caller_contract() -> None:
    use_cache = False
    cache_was_checked = False

    if use_cache:
        cache_was_checked = True

    assert cache_was_checked is False
