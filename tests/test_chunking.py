from src.ingestion.chunking import split_into_sections


def test_each_heading_starts_a_new_section():
    # Each heading starts a new section because a section is a natural unit of meaning.
    text = "# Title\nintro\n## A\ntext a\n## B\ntext b"

    assert split_into_sections(text) == [
        "# Title\nintro",
        "## A\ntext a",
        "## B\ntext b",
    ]
