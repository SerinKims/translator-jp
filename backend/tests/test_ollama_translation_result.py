import asyncio
import os
import sys

from app.llm.ollama_client import OllamaClient
from app.llm.prompts import load_prompt


SAMPLE_JAPANESE_TEXT = (
    "彼は静かに笑った。\n\n"
    "「本当に、それでいいんですか？」\n\n"
    "少女はうなずき、王都の空を見上げた。\n"
)


def test_ollama_translation_result_prints_live_response() -> None:
    # if os.getenv("RUN_OLLAMA_SMOKE") != "1":
    #     pytest.skip("Set RUN_OLLAMA_SMOKE=1 to run the live Ollama smoke test")

    _configure_utf8_output()

    async def run_test() -> None:
        source_text = os.getenv("OLLAMA_TRANSLATION_SAMPLE", SAMPLE_JAPANESE_TEXT)
        system_prompt = load_prompt("translate_ja_ko_v1")
        prompt = f"""다음 일본어 소설 원문을 한국어 웹소설 문체로 번역하세요.
문장을 자연스럽게 연결하고, 한국어 웹소설 스타일에 맞게 번역합니다.

{source_text}"""
        options = {"temperature": 0.2, "max_tokens": 2048}
        client = OllamaClient(options=options)

        result = await client.chat(
            [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": prompt,
                },
            ]
        )

        print("\n=== Ollama Translation Smoke Result ===")
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
