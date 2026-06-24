from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.config import PROJECT_ROOT


UNSUPPORTED_LANGUAGE_PAIR_MESSAGE = "지원하지 않는 번역 언어 조합입니다."

DEFAULT_SOURCE_LANG = "ja"
DEFAULT_TARGET_LANG = "ko"
DEFAULT_PROMPT_VERSION = "translate_ja_ko_v1"


class PromptLoaderError(ValueError):
    """Base error for prompt loading failures."""


class PromptNotFoundError(PromptLoaderError):
    pass


class UnsupportedLanguagePairError(PromptLoaderError):
    pass


@dataclass(frozen=True)
class PromptDefinition:
    version: str
    source_lang: str
    target_lang: str
    filename: str


_PROMPT_DEFINITIONS: dict[tuple[str, str, str], PromptDefinition] = {
    ("ja", "ko", "translate_ja_ko_v1"): PromptDefinition(
        version="translate_ja_ko_v1",
        source_lang="ja",
        target_lang="ko",
        filename="translate_ja_ko_v1.md",
    ),
}

_PROMPT_ALIASES: dict[str, str] = {
    "translate_ja_ko_v1": "translate_ja_ko_v1",
}

_DEFAULT_PROMPTS_BY_LANGUAGE_PAIR: dict[tuple[str, str], str] = {
    ("ja", "ko"): DEFAULT_PROMPT_VERSION,
}


class PromptLoader:
    def __init__(self, prompt_dir: Path | None = None) -> None:
        self.prompt_dir = prompt_dir or PROJECT_ROOT / "harness" / "prompts"

    def select_prompt_version(
        self,
        *,
        source_lang: str = DEFAULT_SOURCE_LANG,
        target_lang: str = DEFAULT_TARGET_LANG,
        prompt_version: str | None = None,
    ) -> str:
        language_pair = (source_lang, target_lang)
        if language_pair not in _DEFAULT_PROMPTS_BY_LANGUAGE_PAIR:
            raise UnsupportedLanguagePairError(UNSUPPORTED_LANGUAGE_PAIR_MESSAGE)

        selected_version = prompt_version or _DEFAULT_PROMPTS_BY_LANGUAGE_PAIR[language_pair]
        return _PROMPT_ALIASES.get(selected_version, selected_version)

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
        definition = _PROMPT_DEFINITIONS.get((source_lang, target_lang, selected_version))
        if definition is None:
            raise PromptNotFoundError(
                f"Prompt version '{prompt_version or selected_version}' not found."
            )

        prompt_path = self.prompt_dir / definition.filename
        if not prompt_path.is_file():
            raise PromptNotFoundError(f"Prompt file not found for version '{definition.version}'.")

        return prompt_path.read_text(encoding="utf-8")


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
