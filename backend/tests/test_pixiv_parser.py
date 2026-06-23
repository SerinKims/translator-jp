import json

import pytest

from app.crawler.pixiv_parser import PixivParseError, parse_pixiv_novel_html


PIXIV_FIXTURE_HTML = """
<!doctype html>
<html>
  <head>
    <meta
      id="meta-preload-data"
      content='{"novel":{"12345678":{"title":"作品タイトル","userName":"作者名","content":"一段落目です。\\n\\n二段落目です。\\n会話文です。"}}}'
    >
  </head>
  <body>
    <nav>UI text that should not be extracted</nav>
    <div id="root"></div>
  </body>
</html>
"""


def test_parse_pixiv_preload_data_preserves_paragraphs() -> None:
    novel = parse_pixiv_novel_html(
        PIXIV_FIXTURE_HTML,
        "https://www.pixiv.net/novel/show.php?id=12345678",
    )

    assert novel.source_site == "pixiv"
    assert novel.source_url == "https://www.pixiv.net/novel/show.php?id=12345678"
    assert novel.source_work_id == "12345678"
    assert novel.title == "作品タイトル"
    assert novel.author == "作者名"
    assert novel.text == "一段落目です。\n\n二段落目です。\n会話文です。"
    assert novel.char_count == len(novel.text)


def test_parse_pixiv_html_fallback_removes_ui_text() -> None:
    html = """
    <html>
      <head><meta property="og:title" content="HTML作品 - pixiv"></head>
      <body>
        <h1>HTML作品</h1>
        <a href="/users/123">HTML作者</a>
        <article data-testid="novel-content">
          <button>Like</button>
          <p>本文一。</p>
          <p>本文二。</p>
        </article>
      </body>
    </html>
    """

    novel = parse_pixiv_novel_html(html, "https://www.pixiv.net/novel/show.php?id=42")

    assert novel.title == "HTML作品"
    assert novel.author == "HTML作者"
    assert novel.text == "本文一。\n本文二。"
    assert "Like" not in novel.text


def test_parse_current_pixiv_ajax_payload_for_user_reference_url() -> None:
    payload = {
        "error": False,
        "message": "",
        "body": {
            "id": "25801711",
            "title": "\u5bfe\u9762",
            "userName": "\u30c1\u30e7\u30b3",
            "content": (
                "\u300c\u4ffa\u3068\u79b0\u8c46\u5b50\u306e\u3088\u3046\u306b\u3001"
                "\u4eba\u3092\u8972\u308f\u306a\u3044\u9b3c\u3092\u9023\u308c\u305f"
                "\u4eba\u304c\u3044\u308b\u3093\u3067\u3059\u304b\uff01\uff1f\u300d"
                "\n\n"
                "\u9b3c\u304c\u51fa\u305f\u3068\u5831\u544a\u304c\u3042\u3063\u305f"
                "\u5834\u6240\u3078\u5411\u304b\u3044\u3001\u8a0e\u4f10\u3057\u305f"
                "\u5f8c\u5831\u544a\u306e\u305f\u3081\u8776\u5c4b\u6577\u3078\u3002"
                "\n\n[newpage]\n\n"
                "\u5f53\u65e5\u3002"
            ),
        },
    }

    novel = parse_pixiv_novel_html(
        json.dumps(payload, ensure_ascii=True),
        "https://www.pixiv.net/novel/show.php?id=25801711",
    )

    assert novel.source_work_id == "25801711"
    assert novel.title == "\u5bfe\u9762"
    assert novel.author == "\u30c1\u30e7\u30b3"
    assert novel.text.startswith("\u300c\u4ffa\u3068\u79b0\u8c46\u5b50")
    assert "\n\n[newpage]\n\n" in novel.text
    assert novel.text.endswith("\u5f53\u65e5\u3002")


def test_parse_pixiv_raises_when_text_is_missing() -> None:
    with pytest.raises(PixivParseError, match="페이지는 열렸지만 소설 원문을 찾지 못했습니다. 원문을 직접 입력해주세요."):
        parse_pixiv_novel_html(
            "<html><body><h1>作品タイトル</h1></body></html>",
            "https://www.pixiv.net/novel/show.php?id=12345678",
        )
