import pytest

from app.llm.prompts import (
    PromptLoader,
    PromptNotFoundError,
    UnsupportedLanguagePairError,
    load_prompt,
)


def test_prompt_file_loads_by_prompt_version() -> None:
    prompt = load_prompt("translate_ja_ko_v1")

    assert "일본어 소설을 한국어 웹소설 문체로 번역" in prompt
    assert "번역문만 출력합니다." in prompt


def test_legacy_translate_ja_ko_v1_loads_ja_ko_prompt() -> None:
    prompt = load_prompt("translate_ja_ko_v1")

    assert "일본어 특유의 말투" in prompt


def test_missing_prompt_version_returns_clear_error() -> None:
    loader = PromptLoader()

    with pytest.raises(PromptNotFoundError, match="Prompt version 'missing_v1' not found"):
        loader.load("missing_v1")


def test_prompt_version_can_be_selected_by_language_pair() -> None:
    loader = PromptLoader()

    assert loader.select_prompt_version(source_lang="ja", target_lang="ko") == "translate_ja_ko_v1"


def test_unsupported_language_pair_returns_clear_error() -> None:
    loader = PromptLoader()

    with pytest.raises(UnsupportedLanguagePairError, match="지원하지 않는 번역 언어 조합입니다."):
        loader.load(source_lang="en", target_lang="ko")
