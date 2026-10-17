import re


# Recognize heading markers once for reuse across every line and document.
_HEADING = re.compile(r"#{1,6} ")


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
