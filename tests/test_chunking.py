from src.ingestion.chunking import split_into_sections, split_long_section


def test_each_heading_starts_a_new_section():
    # Each heading starts a new section because a section is a natural unit of meaning.
    text = "# Title\nintro\n## A\ntext a\n## B\ntext b"

    assert split_into_sections(text) == [
        "# Title\nintro",
        "## A\ntext a",
        "## B\ntext b",
    ]


def test_hash_lines_inside_code_blocks_are_not_headings():
    # Shell comments inside a code fence belong to the example, not a new section.
    text = "# Setup\n\n```\n# install dependencies\npip install x\n```\ndone"

    assert split_into_sections(text) == [text]


def test_hash_without_a_space_is_not_a_heading():
    # A hashtag is plain text, so it must not split the current section.
    text = "# A\n#hashtag\ntext"

    assert split_into_sections(text) == [text]


def test_paragraphs_are_packed_until_the_word_limit():
    # Keep whole paragraphs together while preventing the next one from exceeding the limit.
    section = (
        "one two three four five\n\n"
        "six seven eight nine ten\n\n"
        "eleven twelve thirteen fourteen fifteen"
    )

    assert split_long_section(section, max_words=10) == [
        "one two three four five\n\nsix seven eight nine ten",
        "eleven twelve thirteen fourteen fifteen",
    ]


def test_a_paragraph_longer_than_the_limit_is_kept_whole():
    # Preserve a paragraph's meaning even when it exceeds the soft word limit.
    section = "one two three four five six seven eight nine ten eleven twelve"

    assert split_long_section(section, max_words=5) == [section]
