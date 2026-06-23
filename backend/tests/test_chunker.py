from app.services.chunker import MAX_CHARS_PER_CHUNK, chunk_text


def test_short_text_returns_single_chunk() -> None:
    text = "第一段落です。\n\n第二段落です。"

    chunks = chunk_text(text)

    assert chunks == [
        {
            "index": 0,
            "source_text": text,
            "context_before": "",
            "context_after": "",
        }
    ]


def test_long_text_returns_multiple_chunks() -> None:
    text = "\n\n".join(f"第{i}段落です。これは本文です。" for i in range(10))

    chunks = chunk_text(text, max_chars_per_chunk=50)

    assert len(chunks) > 1
    assert all(len(chunk["source_text"]) <= 50 for chunk in chunks)


def test_paragraph_order_is_preserved() -> None:
    paragraphs = [f"第{i}段落です。" for i in range(8)]

    chunks = chunk_text("\n\n".join(paragraphs), max_chars_per_chunk=30)
    combined = "\n\n".join(chunk["source_text"] for chunk in chunks)

    cursor = -1
    for paragraph in paragraphs:
        next_position = combined.find(paragraph)
        assert next_position > cursor
        cursor = next_position


def test_dialogue_is_not_split_in_the_middle() -> None:
    text = "\n\n".join(
        [
            "地の文です。",
            "「これは大切な台詞です。途中で切れてはいけません」",
            "次の地の文です。",
        ]
    )

    chunks = chunk_text(text, max_chars_per_chunk=35)

    dialogue_chunks = [chunk for chunk in chunks if "「" in chunk["source_text"]]
    assert len(dialogue_chunks) == 1
    assert "」" in dialogue_chunks[0]["source_text"]
    assert "途中で切れてはいけません" in dialogue_chunks[0]["source_text"]


def test_dialogue_lines_without_sentence_endings_split_between_lines() -> None:
    text = "「返事はまだ」\n「それでも待つ」\n「朝まで待つ」"

    chunks = chunk_text(text, max_chars_per_chunk=11)

    assert all(
        chunk["source_text"].count("「") == chunk["source_text"].count("」") for chunk in chunks
    )
    assert [chunk["source_text"] for chunk in chunks] == [
        "「返事はまだ」",
        "「それでも待つ」",
        "「朝まで待つ」",
    ]


def test_japanese_quotes_keep_open_quote_until_it_closes() -> None:
    text = "「これは一つ目の文です。まだ台詞は続きます」彼女は笑った。次の文です。"

    chunks = chunk_text(text, max_chars_per_chunk=28)

    quoted_chunks = [chunk["source_text"] for chunk in chunks if "「" in chunk["source_text"]]
    assert quoted_chunks == ["「これは一つ目の文です。まだ台詞は続きます」"]


def test_overlap_context_is_created_from_adjacent_paragraphs() -> None:
    text = "\n\n".join(["第一段落です。", "第二段落です。", "第三段落です。"])

    chunks = chunk_text(text, max_chars_per_chunk=12, overlap_paragraphs=1)

    assert chunks[0]["context_before"] == ""
    assert chunks[0]["context_after"] == "第二段落です。"
    assert chunks[1]["context_before"] == "第一段落です。"
    assert chunks[1]["context_after"] == "第三段落です。"
    assert chunks[2]["context_before"] == "第二段落です。"
    assert chunks[2]["context_after"] == ""


def test_max_chars_is_not_exceeded() -> None:
    text = "\n\n".join(f"段落{i}です。文章です。" for i in range(20))

    chunks = chunk_text(text, max_chars_per_chunk=40)

    assert MAX_CHARS_PER_CHUNK == 1800
    assert all(len(chunk["source_text"]) <= 40 for chunk in chunks)
