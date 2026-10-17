from src.ingestion.chunking import split_into_sections


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
