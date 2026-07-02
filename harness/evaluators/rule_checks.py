from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


SOURCE_RESIDUAL_CHECK = "no_source_left"
EMPTY_TRANSLATION_CHECK = "empty_translation"
PARAGRAPH_CHECK = "paragraph_count"
DIALOGUE_CHECK = "dialogue_quotes"
GLOSSARY_CHECK = "glossary"
OVER_SUMMARY_CHECK = "over_summary"
PROPER_NOUN_CHECK = "proper_nouns"

CHECK_ORDER = [
    SOURCE_RESIDUAL_CHECK,
    EMPTY_TRANSLATION_CHECK,
    PARAGRAPH_CHECK,
    DIALOGUE_CHECK,
    GLOSSARY_CHECK,
    OVER_SUMMARY_CHECK,
    PROPER_NOUN_CHECK,
]

_HIRAGANA_RE = re.compile(r"[\u3040-\u309f]")
_KATAKANA_RE = re.compile(r"[\u30a0-\u30ff\uff66-\uff9f]")
_CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
_ASCII_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")
_PARAGRAPH_SPLIT_RE = re.compile(r"(?:\r?\n){2,}")


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    score: float
    message: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "score": self.score,
            "message": self.message,
            "details": self.details,
        }


def evaluate_case(case: dict[str, Any], actual: str, *, prompt_version: str) -> dict[str, Any]:
    source = str(case.get("source", ""))
    reference = str(case.get("reference", ""))
    source_lang = str(case.get("source_lang", "ja"))
    target_lang = str(case.get("target_lang", "ko"))
    proper_nouns = _normalize_string_list(case.get("proper_nouns", []))
    glossary = _normalize_glossary(case.get("glossary", []))

    checks = [
        check_no_source_left(actual, source_lang=source_lang, allowed_terms=proper_nouns),
        check_not_empty(actual),
        check_paragraph_count(source, actual),
        check_dialogue_quotes(source, actual),
        check_glossary(source, actual, glossary),
        check_not_over_summarized(source=source, reference=reference, actual=actual),
        check_proper_nouns(actual, proper_nouns=proper_nouns),
    ]
    score = _average(check.score for check in checks)
    passed = all(check.passed for check in checks)

    return {
        "id": str(case.get("id", "")),
        "source_lang": source_lang,
        "target_lang": target_lang,
        "prompt_version": prompt_version,
        "source": source,
        "reference": reference,
        "actual": actual,
        "elapsed_ms": int(case.get("elapsed_ms", 0) or 0),
        "passed": passed,
        "score": round(score, 4),
        "checks": {check.name: check.to_dict() for check in checks},
    }


def check_no_source_left(
    translated_text: str,
    *,
    source_lang: str,
    allowed_terms: list[str] | None = None,
) -> CheckResult:
    checked_text = _remove_allowed_terms(translated_text, allowed_terms or [])
    residuals = _find_source_language_residuals(checked_text, source_lang)
    passed = not residuals
    return CheckResult(
        name=SOURCE_RESIDUAL_CHECK,
        passed=passed,
        score=1.0 if passed else 0.0,
        message="source language residuals were not found"
        if passed
        else "source language residuals remain",
        details={"source_lang": source_lang, "residuals": residuals[:20]},
    )


def check_not_empty(translated_text: str) -> CheckResult:
    passed = bool(translated_text.strip())
    return CheckResult(
        name=EMPTY_TRANSLATION_CHECK,
        passed=passed,
        score=1.0 if passed else 0.0,
        message="translation is not empty" if passed else "translation is empty",
        details={"length": len(translated_text.strip())},
    )


def check_paragraph_count(source_text: str, translated_text: str) -> CheckResult:
    source_count = count_paragraphs(source_text)
    translated_count = count_paragraphs(translated_text)
    passed = source_count == translated_count
    return CheckResult(
        name=PARAGRAPH_CHECK,
        passed=passed,
        score=1.0 if passed else 0.0,
        message="paragraph count matches" if passed else "paragraph count differs",
        details={"source_count": source_count, "translated_count": translated_count},
    )


def check_dialogue_quotes(source_text: str, translated_text: str) -> CheckResult:
    source_count = count_dialogue_segments(source_text)
    translated_count = count_dialogue_segments(translated_text)
    passed = source_count == 0 or source_count == translated_count
    return CheckResult(
        name=DIALOGUE_CHECK,
        passed=passed,
        score=1.0 if passed else 0.0,
        message="dialogue quote count is preserved" if passed else "dialogue quote count differs",
        details={"source_count": source_count, "translated_count": translated_count},
    )


def check_glossary(
    source_text: str,
    translated_text: str,
    glossary: list[dict[str, Any]],
) -> CheckResult:
    violations: list[dict[str, Any]] = []
    applicable = 0
    for term in glossary:
        source_term = str(term.get("source_term", "") or "")
        target_term = str(term.get("target_term", "") or "")
        aliases = _normalize_string_list(term.get("aliases", []))
        is_required = bool(term.get("is_required", True))
        matched_source = _find_first_present(source_text, [source_term, *aliases])
        if not source_term or not target_term or matched_source is None:
            continue
        applicable += 1
        if is_required and target_term not in translated_text:
            violations.append(
                {
                    "source_term": source_term,
                    "target_term": target_term,
                    "matched_source": matched_source,
                }
            )

    passed = not violations
    return CheckResult(
        name=GLOSSARY_CHECK,
        passed=passed,
        score=1.0 if passed else 0.0,
        message="glossary terms are preserved" if passed else "glossary terms are missing",
        details={"applicable_terms": applicable, "violations": violations},
    )


def check_not_over_summarized(
    *,
    source: str,
    reference: str,
    actual: str,
    min_reference_ratio: float = 0.45,
    min_source_ratio: float = 0.25,
) -> CheckResult:
    actual_len = _semantic_length(actual)
    reference_len = _semantic_length(reference)
    source_len = _semantic_length(source)
    if actual_len == 0:
        passed = False
    elif reference_len > 0:
        passed = actual_len >= reference_len * min_reference_ratio
    else:
        passed = actual_len >= source_len * min_source_ratio

    return CheckResult(
        name=OVER_SUMMARY_CHECK,
        passed=passed,
        score=1.0 if passed else 0.0,
        message="translation is not excessively summarized"
        if passed
        else "translation appears excessively summarized",
        details={
            "source_length": source_len,
            "reference_length": reference_len,
            "actual_length": actual_len,
            "min_reference_ratio": min_reference_ratio,
            "min_source_ratio": min_source_ratio,
        },
    )


def check_proper_nouns(translated_text: str, *, proper_nouns: list[str]) -> CheckResult:
    missing = [proper_noun for proper_noun in proper_nouns if proper_noun not in translated_text]
    passed = not missing
    return CheckResult(
        name=PROPER_NOUN_CHECK,
        passed=passed,
        score=1.0 if passed else 0.0,
        message="proper nouns are preserved" if passed else "proper nouns are missing",
        details={"proper_nouns": proper_nouns, "missing": missing},
    )


def count_paragraphs(text: str) -> int:
    paragraphs = [part.strip() for part in _PARAGRAPH_SPLIT_RE.split(text.strip()) if part.strip()]
    return len(paragraphs)


def count_dialogue_segments(text: str) -> int:
    japanese_pairs = min(text.count("「"), text.count("」"))
    curly_pairs = min(text.count("“"), text.count("”"))
    double_quote_pairs = text.count('"') // 2
    return japanese_pairs + curly_pairs + double_quote_pairs


def _find_source_language_residuals(text: str, source_lang: str) -> list[str]:
    if source_lang == "ja":
        return [*sorted(set(_HIRAGANA_RE.findall(text))), *sorted(set(_KATAKANA_RE.findall(text)))]
    if source_lang in {"zh-CN", "zh-TW"}:
        return sorted(set(_CJK_RE.findall(text)))
    if source_lang == "en":
        return sorted(set(match.group(0) for match in _ASCII_WORD_RE.finditer(text)))
    return []


def _remove_allowed_terms(text: str, allowed_terms: list[str]) -> str:
    cleaned = text
    for term in sorted((term for term in allowed_terms if term), key=len, reverse=True):
        cleaned = cleaned.replace(term, "")
    return cleaned


def _normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _normalize_glossary(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _find_first_present(text: str, expressions: list[str]) -> str | None:
    for expression in expressions:
        if expression and expression in text:
            return expression
    return None


def _semantic_length(text: str) -> int:
    return sum(1 for char in text if not char.isspace())


def _average(values: Any) -> float:
    items = list(values)
    if not items:
        return 0.0
    return sum(items) / len(items)
