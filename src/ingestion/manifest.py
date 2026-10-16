import csv
import hashlib
import re
from collections import deque
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from itertools import islice
from types import MappingProxyType

from src.ingestion.departments import department_for


_LINK_ONLY_LINE = re.compile(r"^\s*[-*+]?\s*\[[^\]]*\]\([^)]*\)\s*$")
_INLINE_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")


@dataclass(frozen=True)
class PageCandidate:
    source_path: str
    department: str
    words: int
    sha256: str


DEFAULT_SELECTION_TARGETS: Mapping[str, int] = MappingProxyType(
    {
        "engineering": 60,
        "finance": 35,
        "people": 50,
        "onboarding": 5,
        "general": 40,
    }
)


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


def _spread_pages(pages: list[PageCandidate], depth: int = 0) -> Iterator[PageCandidate]:
    """Rotate through sibling folders, including nested topics and direct files."""
    groups: dict[str, list[PageCandidate]] = {}
    for page in pages:
        parts = page.source_path.split("/")
        # Direct files share a bucket so a folder's index pages cannot crowd out its children.
        key = parts[depth] if len(parts) > depth + 1 else ""
        groups.setdefault(key, []).append(page)

    # Sorting both folders and input pages makes selection independent of discovery order.
    streams = deque(
        iter(groups[key]) if key == "" else _spread_pages(groups[key], depth + 1)
        for key in sorted(groups)
    )
    while streams:
        stream = streams.popleft()
        try:
            page = next(stream)
        except StopIteration:
            # Exhausted folders leave the rotation; larger folders can fill remaining slots.
            continue
        yield page
        streams.append(stream)


def select_pages(
    candidates: Iterable[PageCandidate],
    targets: Mapping[str, int] = DEFAULT_SELECTION_TARGETS,
    minimum_words: int = 150,
) -> tuple[PageCandidate, ...]:
    eligible = sorted(
        (candidate for candidate in candidates if candidate.words >= minimum_words),
        key=lambda candidate: candidate.source_path,
    )
    selected: list[PageCandidate] = []

    for department, target in targets.items():
        if target < 0:
            raise ValueError(f"Selection target cannot be negative: {department}")

        department_pages = [candidate for candidate in eligible if candidate.department == department]
        if len(department_pages) < target:
            raise ValueError(f"Not enough eligible pages for department: {department}")
        # Apply the quota after spreading; keep the final CSV sorted for readable diffs.
        selected.extend(islice(_spread_pages(department_pages), target))

    return tuple(sorted(selected, key=lambda candidate: candidate.source_path))


def write_manifest(rows: Iterable[PageCandidate], output_path: Path) -> None:
    ordered_rows = sorted(rows, key=lambda row: row.source_path)
    source_paths = [row.source_path for row in ordered_rows]
    if len(source_paths) != len(set(source_paths)):
        raise ValueError("Manifest rows must have unique source paths")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("source_path", "department", "sha256"),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(
            {
                "source_path": row.source_path,
                "department": row.department,
                "sha256": row.sha256,
            }
            for row in ordered_rows
        )


def build_manifest(
    source_root: Path,
    output_path: Path,
    targets: Mapping[str, int] = DEFAULT_SELECTION_TARGETS,
    minimum_words: int = 150,
) -> tuple[PageCandidate, ...]:
    candidates: list[PageCandidate] = []
    for path in source_root.rglob("*.md"):
        source_path = path.relative_to(source_root).as_posix()
        try:
            department = department_for(source_path)
        except ValueError:
            continue

        words = real_word_count(path.read_text(encoding="utf-8"))
        if words < minimum_words:
            continue
        candidates.append(PageCandidate(source_path, department, words, file_sha256(path)))

    selected = select_pages(candidates, targets=targets, minimum_words=minimum_words)
    write_manifest(selected, output_path)
    return selected
