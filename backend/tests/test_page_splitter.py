from app.services.page_splitter import has_newpage_marker, split_pages


def test_split_text_without_newpage_returns_single_page() -> None:
    pages = split_pages("第一話の本文")

    assert has_newpage_marker("第一話の本文") is False
    assert len(pages) == 1
    assert pages[0].page_index == 0
    assert pages[0].source_text == "第一話の本文"


def test_split_text_with_newpage_returns_multiple_pages() -> None:
    pages = split_pages("一ページ目[newpage]二ページ目[newpage]三ページ目")

    assert len(pages) == 3
    assert [page.page_index for page in pages] == [0, 1, 2]
    assert [page.source_text for page in pages] == ["一ページ目", "二ページ目", "三ページ目"]


def test_split_text_removes_empty_pages() -> None:
    pages = split_pages("[newpage] 一ページ目 [newpage]   [newpage]\n二ページ目\n")

    assert len(pages) == 2
    assert [page.page_index for page in pages] == [0, 1]
    assert [page.source_text for page in pages] == ["一ページ目", "二ページ目"]
