import pytest

from src.ingestion.manifest import file_sha256, real_word_count


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


@pytest.mark.parametrize(
    "text, expected",
    [
        ("[](https://x.com/page) word", 1),
        ("[→](https://x.com/page) next", 1),
    ],
)
def test_link_urls_never_count_as_words(text, expected):
    assert real_word_count(text) == expected


def test_sha256_of_known_text(tmp_path):
    file = tmp_path / "a.md"
    file.write_bytes(b"hello")

    assert file_sha256(file) == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"


def test_sha256_normalizes_line_endings(tmp_path):
    unix_file = tmp_path / "unix.md"
    windows_file = tmp_path / "windows.md"
    unix_file.write_bytes(b"a\nb\n")
    windows_file.write_bytes(b"a\r\nb\r\n")

    assert file_sha256(unix_file) == file_sha256(windows_file)


def test_sha256_differs_for_different_text(tmp_path):
    first_file = tmp_path / "first.md"
    second_file = tmp_path / "second.md"
    first_file.write_bytes(b"first")
    second_file.write_bytes(b"second")

    assert file_sha256(first_file) != file_sha256(second_file)


def test_sha256_handles_utf8_text(tmp_path):
    file = tmp_path / "cafe.md"
    file.write_bytes("café".encode("utf-8"))

    assert file_sha256(file) == "850f7dc43910ff890f8879c0ed26fe697c93a067ad93a7d50f466a7028a9bf4e"
    assert file_sha256(file) == file_sha256(file)


def test_sha256_missing_file_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        file_sha256(tmp_path / "missing.md")
