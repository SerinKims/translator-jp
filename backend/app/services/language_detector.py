from __future__ import annotations

from dataclasses import dataclass

SUPPORTED_SOURCE_LANGS = {"auto", "ja", "zh-CN", "zh-TW", "en"}
TRANSLATABLE_SOURCE_LANGS = {"ja", "zh-CN", "zh-TW", "en"}
SUPPORTED_TARGET_LANGS = {"ko"}

UNKNOWN_LANG = "unknown"

TRADITIONAL_CHINESE_HINTS = set(
    "們個國學體後來時會說對過還這裡為與無麼開關見聽長門風雲龍鳳劍氣靈臺萬"
)


@dataclass(frozen=True)
class LanguageDetectionResult:
    language: str
    confidence: float


def detect_language(text: str) -> LanguageDetectionResult:
    stripped = text.strip()
    if not stripped:
        return LanguageDetectionResult(UNKNOWN_LANG, 0.0)

    kana_count = sum(1 for char in stripped if _is_hiragana(char) or _is_katakana(char))
    cjk_count = sum(1 for char in stripped if _is_cjk(char))
    alpha_count = sum(1 for char in stripped if char.isascii() and char.isalpha())
    signal_count = sum(1 for char in stripped if _is_signal_char(char))

    if kana_count > 0:
        confidence = _bounded_confidence(0.78 + min(kana_count / max(signal_count, 1), 0.2))
        return LanguageDetectionResult("ja", confidence)

    if cjk_count > 0:
        cjk_ratio = cjk_count / max(signal_count, 1)
        if cjk_ratio >= 0.2:
            language = "zh-TW" if _has_traditional_hint(stripped) else "zh-CN"
            confidence = _bounded_confidence(0.65 + min(cjk_ratio, 0.3))
            return LanguageDetectionResult(language, confidence)

    if alpha_count > 0:
        alpha_ratio = alpha_count / max(signal_count, 1)
        cjk_ratio = cjk_count / max(signal_count, 1)
        if alpha_ratio >= 0.55 and cjk_ratio <= 0.05:
            confidence = _bounded_confidence(0.65 + min(alpha_ratio - 0.55, 0.3))
            return LanguageDetectionResult("en", confidence)

    return LanguageDetectionResult(UNKNOWN_LANG, 0.0)


def _is_hiragana(char: str) -> bool:
    return "\u3040" <= char <= "\u309f"


def _is_katakana(char: str) -> bool:
    return "\u30a0" <= char <= "\u30ff" or "\uff66" <= char <= "\uff9f"


def _is_cjk(char: str) -> bool:
    return (
        "\u3400" <= char <= "\u4dbf" or "\u4e00" <= char <= "\u9fff" or "\uf900" <= char <= "\ufaff"
    )


def _is_signal_char(char: str) -> bool:
    return char.isalpha() or _is_cjk(char) or _is_hiragana(char) or _is_katakana(char)


def _has_traditional_hint(text: str) -> bool:
    return any(char in TRADITIONAL_CHINESE_HINTS for char in text)


def _bounded_confidence(value: float) -> float:
    return round(min(max(value, 0.0), 0.99), 2)
