import pytest

from app.llm.prompts import (
    PromptLoader,
    PromptNotFoundError,
    UnsupportedLanguagePairError,
    load_prompt,
)


def test_prompt_file_loads_by_prompt_version() -> None:
    prompt = load_prompt("translate_ja_ko_v1")

    assert prompt.strip()


def test_missing_prompt_version_returns_clear_error() -> None:
    loader = PromptLoader()

    with pytest.raises(PromptNotFoundError, match="Prompt version 'missing_v1' not found"):
        loader.load("missing_v1")


def test_prompt_version_can_be_selected_by_language_pair() -> None:
    loader = PromptLoader()

    assert loader.select_prompt_version(source_lang="ja", target_lang="ko") == "translate_ja_ko_v1"
    assert (
        loader.select_prompt_version(source_lang="zh-CN", target_lang="ko") == "translate_zh_ko_v1"
    )
    assert (
        loader.select_prompt_version(source_lang="zh-TW", target_lang="ko") == "translate_zh_ko_v1"
    )
    assert loader.select_prompt_version(source_lang="en", target_lang="ko") == "translate_en_ko_v1"


def test_global_ja_default_falls_back_to_language_pair_default() -> None:
    loader = PromptLoader()

    assert (
        loader.select_prompt_version(
            source_lang="en",
            target_lang="ko",
            prompt_version="translate_ja_ko_v1",
        )
        == "translate_en_ko_v1"
    )


def test_unsupported_language_pair_returns_clear_error() -> None:
    loader = PromptLoader()

    with pytest.raises(UnsupportedLanguagePairError, match="지원하지 않는 번역 언어 조합입니다."):
        loader.load(source_lang="fr", target_lang="ko")
