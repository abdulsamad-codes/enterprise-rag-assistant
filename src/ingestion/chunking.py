import re
from dataclasses import dataclass

from src.core.config import KNOWN_DEPARTMENTS


# Recognize heading markers once for reuse across every line and document.
_HEADING = re.compile(r"#{1,6} ")


def strip_front_matter(text: str) -> str:
    # Keep line endings so removing metadata does not rewrite the remaining body.
    lines = text.splitlines(keepends=True)
    # Only a delimiter on the first line at column zero can open front matter.
    if lines and lines[0].rstrip() == "---":
        # Start after the opening line and stop at the first whole closing delimiter.
        for index in range(1, len(lines)):
            if lines[index].rstrip() == "---":
                # Reuse the original line endings, including any trailing newline.
                return "".join(lines[index + 1:])

    # Missing or unclosed metadata must leave the original content untouched.
    return text


# Freeze labels and text so later pipeline stages cannot accidentally reassign them.
@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_id: str
    department: str
    text: str


def chunk_document(
    source_path: str, department: str, text: str, max_words: int = 300
) -> list[Chunk]:
    # Reject a bad label before any splitting occurs or any chunk can exist.
    if department not in KNOWN_DEPARTMENTS:
        raise ValueError(f"Unknown department: {department!r}")

    # Split at headings first, then pack each section without mixing separate topics.
    pieces = []
    for section in split_into_sections(text):
        pieces.extend(split_long_section(section, max_words))

    # Source-based IDs are repeatable for unchanged input and distinguish pages without randomness.
    return [
        Chunk(
            chunk_id=f"{source_path}#{index:03d}",
            document_id=source_path,
            # Preserve the supplied manifest department for later access filtering.
            department=department,
            text=piece,
        )
        for index, piece in enumerate(pieces)
    ]


def split_into_sections(text: str) -> list[str]:
    # Keep finished sections separate from the lines still being collected.
    sections = []
    current = []
    # Remember whether lines belong to a code example rather than document headings.
    in_code_block = False

    # Read one line at a time so headings can mark section boundaries.
    for line in text.splitlines():
        # Opening and closing backtick fences switch how subsequent lines are treated.
        if line.strip().startswith("```"):
            in_code_block = not in_code_block

        # Save existing content before a new heading, avoiding an empty first section.
        # Hash lines inside code examples must stay in the current section.
        if _HEADING.match(line) and not in_code_block and current:
            sections.append("\n".join(current))
            current = []

        # Keep every line, including the heading that begins a section.
        current.append(line)

    # The final section has no following heading to trigger saving it in the loop.
    if current:
        sections.append("\n".join(current))

    # Return the completed sections for later chunking stages.
    return sections


def split_long_section(section: str, max_words: int) -> list[str]:
    # Use paragraph boundaries to keep related sentences together.
    paragraphs = section.split("\n\n")
    # Track finished pieces separately from the paragraphs and word count being collected.
    pieces = []
    current = []
    current_words = 0

    for paragraph in paragraphs:
        # Count whitespace-separated words to measure the piece against the soft limit.
        words = len(paragraph.split())
        # Save existing paragraphs before the next one would exceed the limit.
        if current and current_words + words > max_words:
            pieces.append("\n\n".join(current))
            current = []
            current_words = 0

        # Keep each paragraph whole, even when it alone exceeds the soft limit.
        current.append(paragraph)
        current_words += words

    # The last piece has no following paragraph to trigger saving it in the loop.
    if current:
        pieces.append("\n\n".join(current))

    # Return the packed pieces for later chunking stages.
    return pieces
