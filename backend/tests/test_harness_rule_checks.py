from __future__ import annotations

from harness.evaluators.rule_checks import (
    check_dialogue_quotes,
    check_glossary,
    check_no_source_left,
    check_not_empty,
    check_not_over_summarized,
    check_paragraph_count,
    check_proper_nouns,
    evaluate_case,
)


def test_detects_japanese_residual_text() -> None:
    result = check_no_source_left("그는 まだ 끝나지 않았다고 말했다.", source_lang="ja")

    assert result.passed is False
    assert "ま" in result.details["residuals"]


def test_detects_chinese_residual_text() -> None:
    result = check_no_source_left("그는 安静地 웃었다.", source_lang="zh-CN")

    assert result.passed is False
    assert "安" in result.details["residuals"]


def test_detects_english_residual_text() -> None:
    result = check_no_source_left("그는 smiled quietly.", source_lang="en")

    assert result.passed is False
    assert "smiled" in result.details["residuals"]


def test_allows_english_proper_nouns_for_english_residual_check() -> None:
    result = check_no_source_left(
        "Raven은 문 앞에서 기다렸다.",
        source_lang="en",
        allowed_terms=["Raven"],
    )

    assert result.passed is True


def test_detects_empty_translation() -> None:
    result = check_not_empty("   \n")

    assert result.passed is False


def test_compares_paragraph_counts() -> None:
    result = check_paragraph_count("첫 문단\n\n둘째 문단", "첫 문단 둘째 문단")

    assert result.passed is False
    assert result.details["source_count"] == 2
    assert result.details["translated_count"] == 1


def test_detects_missing_dialogue_quotes() -> None:
    result = check_dialogue_quotes("「まだです」彼女は 말했다.", "아직이에요, 그녀는 말했다.")

    assert result.passed is False


def test_detects_glossary_violation() -> None:
    result = check_glossary(
        "魔王は王都を見た。",
        "마왕은 수도를 보았다.",
        [
            {"source_term": "魔王", "target_term": "마왕"},
            {"source_term": "王都", "target_term": "왕도"},
        ],
    )

    assert result.passed is False
    assert result.details["violations"] == [
        {"source_term": "王都", "target_term": "왕도", "matched_source": "王都"}
    ]


def test_detects_excessive_summary() -> None:
    result = check_not_over_summarized(
        source="그는 긴 복도를 지나 문 앞에 멈춰 섰다.",
        reference="그는 긴 복도를 지나 차가운 문 앞에 조용히 멈춰 섰다.",
        actual="멈췄다.",
    )

    assert result.passed is False


def test_detects_missing_proper_noun() -> None:
    result = check_proper_nouns("그는 성문 앞에서 기다렸다.", proper_nouns=["Raven"])

    assert result.passed is False
    assert result.details["missing"] == ["Raven"]


def test_evaluate_case_combines_rule_results() -> None:
    case = {
        "id": "ja_case",
        "source_lang": "ja",
        "target_lang": "ko",
        "source": "「姫様」",
        "reference": "“공주님.”",
        "glossary": [{"source_term": "姫様", "target_term": "공주님"}],
    }

    result = evaluate_case(case, "“공주님.”", prompt_version="translate_ja_ko_v1")

    assert result["passed"] is True
    assert result["checks"]["glossary"]["passed"] is True
    assert result["checks"]["dialogue_quotes"]["passed"] is True
