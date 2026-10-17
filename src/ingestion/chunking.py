def split_into_sections(text: str) -> list[str]:
    # Keep finished sections separate from the lines still being collected.
    sections = []
    current = []

    # Read one line at a time so headings can mark section boundaries.
    for line in text.splitlines():
        # Save existing content before a new heading, avoiding an empty first section.
        if line.startswith("#") and current:
            sections.append("\n".join(current))
            current = []

        # Keep every line, including the heading that begins a section.
        current.append(line)

    # The final section has no following heading to trigger saving it in the loop.
    if current:
        sections.append("\n".join(current))

    # Return the completed sections for later chunking stages.
    return sections
