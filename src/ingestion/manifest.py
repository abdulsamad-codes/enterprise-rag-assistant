import hashlib
import re
from pathlib import Path


_LINK_ONLY_LINE = re.compile(r"^\s*[-*+]?\s*\[[^\]]*\]\([^)]*\)\s*$")
_INLINE_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def real_word_count(text: str) -> int:
    lines = text.splitlines()
    start = 0

    # Front matter is metadata, so skip it only when it starts on the first line.
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                start = index + 1
                break

    body = []
    for line in lines[start:]:
        # Hugo shortcode lines are template code, not readable page content.
        if line.lstrip().startswith("{{") or _LINK_ONLY_LINE.fullmatch(line):
            continue
        # Keep link text while removing URLs so links do not inflate the count.
        body.append(_INLINE_LINK.sub(r"\1", line))

    return sum(any(character.isalnum() for character in piece) for piece in "\n".join(body).split())


def file_sha256(path: Path) -> str:
    data = path.read_bytes()
    # Hash LF-normalized bytes so Windows and Linux copies share one fingerprint.
    normalized_data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(normalized_data).hexdigest()
