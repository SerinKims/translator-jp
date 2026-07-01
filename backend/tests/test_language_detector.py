from app.services.language_detector import UNKNOWN_LANG, detect_language


def test_detects_japanese_when_kana_is_present() -> None:
    result = detect_language("彼は静かに目を閉じた。これは夢ではない。")

    assert result.language == "ja"
    assert result.confidence > 0


def test_detects_simplified_chinese_for_cjk_without_kana() -> None:
    result = detect_language("他静静地闭上了眼睛。门外传来了脚步声。")

    assert result.language == "zh-CN"
    assert result.confidence > 0


def test_detects_traditional_chinese_when_traditional_hints_are_present() -> None:
    result = detect_language("他靜靜地關上門，雲霧在長街盡頭翻湧。")

    assert result.language == "zh-TW"
    assert result.confidence > 0


def test_detects_english_when_alphabet_ratio_is_high() -> None:
    result = detect_language("The knight closed his eyes and waited for dawn.")

    assert result.language == "en"
    assert result.confidence > 0


def test_returns_unknown_when_no_language_signal_exists() -> None:
    result = detect_language("12345 !!!")

    assert result.language == UNKNOWN_LANG
    assert result.confidence == 0.0
