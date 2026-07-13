from __future__ import annotations

import re
from pathlib import Path

from app.core.config import PROJECT_ROOT, get_settings

UNSUPPORTED_LANGUAGE_PAIR_MESSAGE = "지원하지 않는 번역 언어 조합입니다."

DEFAULT_SOURCE_LANG = "ja"
DEFAULT_TARGET_LANG = "ko"
DEFARULT_JA_PROMPT_VERSION = "translate_ja_ko_v1"
DEFAULT_ZH_PROMPT_VERSION = "translate_zh_ko_v1"
DEFAULT_EN_PROMPT_VERSION = "translate_en_ko_v1"
PROMPT_VERSION_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


class PromptLoaderError(ValueError):
    """Base error for prompt loading failures."""


class PromptNotFoundError(PromptLoaderError):
    pass


class UnsupportedLanguagePairError(PromptLoaderError):
    pass


SUPPORTED_LANGUAGE_PAIR_PREFIXES: dict[tuple[str, str], str] = {
    ("ja", "ko"): "translate_ja_ko_",
    ("zh-CN", "ko"): "translate_zh_ko_",
    ("zh-TW", "ko"): "translate_zh_ko_",
    ("en", "ko"): "translate_en_ko_",
}


class PromptLoader:
    def __init__(
        self,
        prompt_dir: Path | None = None,
        *,
        default_prompt_versions: dict[tuple[str, str], str] | None = None,
    ) -> None:
        self.prompt_dir = prompt_dir or PROJECT_ROOT / "harness" / "prompts"
        self.default_prompt_versions = default_prompt_versions or self._defaults_from_settings()

    def select_prompt_version(
        self,
        *,
        source_lang: str = DEFAULT_SOURCE_LANG,
        target_lang: str = DEFAULT_TARGET_LANG,
        prompt_version: str | None = None,
    ) -> str:
        language_pair = (source_lang, target_lang)
        expected_prefix = SUPPORTED_LANGUAGE_PAIR_PREFIXES.get(language_pair)
        if expected_prefix is None:
            raise UnsupportedLanguagePairError(UNSUPPORTED_LANGUAGE_PAIR_MESSAGE)

        selected_version = prompt_version or self.default_prompt_versions[language_pair]
        self._validate_prompt_version(
            selected_version,
            expected_prefix=expected_prefix,
        )
        return selected_version

    def load(
        self,
        prompt_version: str | None = None,
        *,
        source_lang: str = DEFAULT_SOURCE_LANG,
        target_lang: str = DEFAULT_TARGET_LANG,
    ) -> str:
        selected_version = self.select_prompt_version(
            source_lang=source_lang,
            target_lang=target_lang,
            prompt_version=prompt_version,
        )
        prompt_path = self.prompt_dir / f"{selected_version}.md"
        if not prompt_path.is_file():
            raise PromptNotFoundError(f"Prompt file not found for version '{selected_version}'.")

        return prompt_path.read_text(encoding="utf-8")

    def _defaults_from_settings(self) -> dict[tuple[str, str], str]:
        settings = get_settings()
        ja_prompt_version = settings.prompt_version_ja_ko or DEFARULT_JA_PROMPT_VERSION
        zh_prompt_version = settings.prompt_version_zh_ko or DEFAULT_ZH_PROMPT_VERSION
        en_prompt_version = settings.prompt_version_en_ko or DEFAULT_EN_PROMPT_VERSION
        return {
            ("ja", "ko"): ja_prompt_version,
            ("zh-CN", "ko"): zh_prompt_version,
            ("zh-TW", "ko"): zh_prompt_version,
            ("en", "ko"): en_prompt_version,
        }

    def _validate_prompt_version(self, prompt_version: str, *, expected_prefix: str) -> None:
        if not PROMPT_VERSION_PATTERN.fullmatch(prompt_version) or not prompt_version.startswith(
            expected_prefix
        ):
            raise PromptNotFoundError(f"Prompt version '{prompt_version}' not found.")


def load_prompt(
    prompt_version: str | None = None,
    *,
    source_lang: str = DEFAULT_SOURCE_LANG,
    target_lang: str = DEFAULT_TARGET_LANG,
) -> str:
    return PromptLoader().load(
        prompt_version=prompt_version,
        source_lang=source_lang,
        target_lang=target_lang,
    )
