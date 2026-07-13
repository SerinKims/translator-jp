from pathlib import Path

import pytest

from app.core.config import get_settings
from app.llm.prompts import (
    PromptLoader,
    PromptNotFoundError,
    UnsupportedLanguagePairError,
    load_prompt,
)

DEFAULT_PROMPTS = {
    ("ja", "ko"): "translate_ja_ko_v1",
    ("zh-CN", "ko"): "translate_zh_ko_v1",
    ("zh-TW", "ko"): "translate_zh_ko_v1",
    ("en", "ko"): "translate_en_ko_v1",
}


def test_prompt_file_loads_by_prompt_version() -> None:
    prompt = load_prompt("translate_ja_ko_v1")

    assert prompt.strip()


def test_missing_prompt_version_returns_clear_error(tmp_path: Path) -> None:
    loader = PromptLoader(
        prompt_dir=tmp_path,
        default_prompt_versions=DEFAULT_PROMPTS,
    )

    with pytest.raises(PromptNotFoundError, match="Prompt file not found"):
        loader.load("translate_ja_ko_v9")


def test_prompt_version_can_be_selected_by_language_pair() -> None:
    loader = PromptLoader(default_prompt_versions=DEFAULT_PROMPTS)

    assert loader.select_prompt_version(source_lang="ja", target_lang="ko") == "translate_ja_ko_v1"
    assert (
        loader.select_prompt_version(source_lang="zh-CN", target_lang="ko") == "translate_zh_ko_v1"
    )
    assert (
        loader.select_prompt_version(source_lang="zh-TW", target_lang="ko") == "translate_zh_ko_v1"
    )
    assert loader.select_prompt_version(source_lang="en", target_lang="ko") == "translate_en_ko_v1"


def test_mismatched_prompt_version_is_rejected() -> None:
    loader = PromptLoader(default_prompt_versions=DEFAULT_PROMPTS)

    with pytest.raises(PromptNotFoundError, match="Prompt version 'translate_ja_ko_v1' not found"):
        loader.select_prompt_version(
            source_lang="en",
            target_lang="ko",
            prompt_version="translate_ja_ko_v1",
        )


def test_load_without_prompt_version_uses_language_pair_default() -> None:
    loader = PromptLoader(default_prompt_versions=DEFAULT_PROMPTS)

    prompt = loader.load(source_lang="en", target_lang="ko")

    assert prompt.strip()
    assert loader.select_prompt_version(source_lang="en", target_lang="ko") == "translate_en_ko_v1"


def test_dynamic_prompt_file_loads_without_prompt_definition(tmp_path: Path) -> None:
    prompt_path = tmp_path / "translate_en_ko_v2.md"
    prompt_path.write_text("dynamic english prompt", encoding="utf-8")
    loader = PromptLoader(
        prompt_dir=tmp_path,
        default_prompt_versions={**DEFAULT_PROMPTS, ("en", "ko"): "translate_en_ko_v2"},
    )

    assert loader.load(source_lang="en", target_lang="ko") == "dynamic english prompt"


def test_env_prompt_versions_drive_language_pair_defaults(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PROMPT_VERSION_JA_KO", "translate_ja_ko_v2")
    monkeypatch.setenv("PROMPT_VERSION_ZH_KO", "translate_zh_ko_v2")
    monkeypatch.setenv("PROMPT_VERSION_EN_KO", "translate_en_ko_v2")
    get_settings.cache_clear()

    try:
        for version in (
            "translate_ja_ko_v2",
            "translate_zh_ko_v2",
            "translate_en_ko_v2",
        ):
            (tmp_path / f"{version}.md").write_text(version, encoding="utf-8")

        loader = PromptLoader(prompt_dir=tmp_path)

        assert loader.load(source_lang="ja", target_lang="ko") == "translate_ja_ko_v2"
        assert loader.load(source_lang="zh-CN", target_lang="ko") == "translate_zh_ko_v2"
        assert loader.load(source_lang="zh-TW", target_lang="ko") == "translate_zh_ko_v2"
        assert loader.load(source_lang="en", target_lang="ko") == "translate_en_ko_v2"
    finally:
        get_settings.cache_clear()


def test_legacy_prompt_version_env_is_japanese_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PROMPT_VERSION", "translate_ja_ko_v2")
    monkeypatch.delenv("PROMPT_VERSION_JA_KO", raising=False)
    get_settings.cache_clear()

    try:
        (tmp_path / "translate_ja_ko_v2.md").write_text("legacy ja prompt", encoding="utf-8")
        (tmp_path / "translate_en_ko_v1.md").write_text("default en prompt", encoding="utf-8")

        loader = PromptLoader(prompt_dir=tmp_path)

        assert loader.load(source_lang="ja", target_lang="ko") == "legacy ja prompt"
        assert loader.load(source_lang="en", target_lang="ko") == "default en prompt"
    finally:
        get_settings.cache_clear()


def test_unsupported_language_pair_returns_clear_error() -> None:
    loader = PromptLoader(default_prompt_versions=DEFAULT_PROMPTS)

    with pytest.raises(UnsupportedLanguagePairError, match="지원하지 않는 번역 언어 조합입니다."):
        loader.load(source_lang="fr", target_lang="ko")
