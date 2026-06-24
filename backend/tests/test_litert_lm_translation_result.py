import asyncio
import os
import sys

import pytest

from app.llm.litert_lm_client import LiteRTLMClient
from app.llm.prompts import load_prompt


SAMPLE_JAPANESE_TEXT = (
    "「なぁ、お前、行く所ないならおれ達と来ないか？」\n\n"
    "その男─シャンクスさんはそう言って何もかも無くしたオレに手を差し伸べてくれた。\n\n"
    "その日からオレは赤髪海賊団の一員になった。\n\n"
)


# SAMPLE_JAPANESE_TEXT = (
#     "「猗窩座さん、このお召し物はどうですか？」\n",
#     "「んーん」\n",
#     "「ではこちらは？」\n",
#     "「んー！」]\n",
#     "幼少期に俺と猗窩座が着ていた洋服や和服を箪笥から引っ張り出しどれを着たいか尋ねる恋雪さんと何を出されても首を横に振る猗窩座を見守りながら自身の準備を進める。\n"
# )


def test_litert_lm_translation_result_prints_live_response() -> None:
    if os.getenv("RUN_LITERT_LM_SMOKE") != "1":
        pytest.skip("Set RUN_LITERT_LM_SMOKE=1 to run the live LiteRT-LM smoke test")

    _configure_utf8_output()

    async def run_test() -> None:
        source_text = os.getenv("LITERT_LM_TRANSLATION_SAMPLE", SAMPLE_JAPANESE_TEXT)
        system_prompt = load_prompt("translate_ja_ko_v1")
        prompt = f"""다음 일본어 소설 원문을 한국어 웹소설 문체로 번역하세요.
        문장을 자연스럽게 연결하고, 한국어 웹소설 스타일에 맞게 번역합니다.
        {source_text}"""

        client = LiteRTLMClient()

        result = await client.chat(
            [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": prompt,
                },
            ]
        )

        print("\n=== LiteRT-LM Translation Smoke Result ===")
        print(f"model: {result.model}")
        print(f"elapsed_ms: {result.elapsed_ms}")
        print("\n[source]")
        print(source_text)
        print("\n[translation]")
        print(result.content)
        print("======================================\n")

        assert result.content
        assert result.elapsed_ms >= 0

    asyncio.run(run_test())


def _configure_utf8_output() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
