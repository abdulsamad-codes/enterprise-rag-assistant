import pytest

from src.ingestion.manifest import real_word_count


@pytest.mark.parametrize(
    "text, expected",
    [
        ("", 0),
        ("one two three", 3),
    ],
)
def test_counts_plain_text(text, expected):
    assert real_word_count(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("---\ntitle: X\n---\nhello world", 2),
        ("hello\n---\nworld", 2),
        ("---\ntitle: x\nhello", 3),
    ],
)
def test_front_matter_and_horizontal_rules_are_handled(text, expected):
    assert real_word_count(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("[Docs](https://x.com)", 0),
        ("- [Docs](https://x.com)", 0),
        ("See [Docs](https://x.com) for more", 4),
    ],
)
def test_links_are_counted_only_when_part_of_real_text(text, expected):
    assert real_word_count(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("{{< note >}}\nreal text", 2),
        ("## Title\nsome text", 3),
        ("a\r\nb", 2),
    ],
)
def test_templates_markdown_symbols_and_line_endings_are_handled(text, expected):
    assert real_word_count(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("one  two\tthree\n", 3),
        ("- item one", 2),
        ("   \n\n", 0),
        ("| a | b |\n| --- | --- |", 2),
    ],
)
def test_whitespace_markers_and_tables_are_handled(text, expected):
    assert real_word_count(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("---\r\ntitle: x\r\n---\r\nhello", 1),
        ("---\na: b\n---\nhello\n---\nworld", 2),
        ("---\n---\ntext", 1),
    ],
)
def test_front_matter_edge_cases_are_handled(text, expected):
    assert real_word_count(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("[Docs](https://x.com) and [More](https://y.com)", 3),
        ("[A](x) real sentence follows [B](y)", 5),
        ("+ [Docs](https://x.com)", 0),
    ],
)
def test_link_lines_with_real_text_are_counted(text, expected):
    assert real_word_count(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("don't stop", 2),
        ("visit https://handbook.gitlab.com/handbook/ today", 3),
        ("use my_var_name here", 3),
        ("well-known fact", 2),
    ],
)
def test_words_are_whitespace_separated(text, expected):
    assert real_word_count(text) == expected
