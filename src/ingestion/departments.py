from collections.abc import Mapping
from types import MappingProxyType

# Excluded path prefixes (stored in lowercase for case-insensitive matching)
EXCLUDED_PREFIXES: tuple[tuple[str, ...], ...] = (
    ("finance", "readmes"),
    ("finance", "jihu-support"),
)

# Source-of-truth folder mapping table (path tuple -> department)
_MAPPING_DATA: dict[tuple[str, ...], str] = {
    ("people-group", "general-onboarding"): "onboarding",
    ("people-group", "general-onboarding", "tanewki-tips.md"): "people",
    ("people-group", "general-onboarding", "_index.md"): "people",
    ("eta", "corporate-it", "end-user-services", "onboarding101"): "onboarding",
    ("people-group",): "people",
    ("people-policies",): "people",
    ("total-rewards",): "people",
    ("hiring",): "people",
    ("labor-and-employment-notices",): "people",
    ("finance",): "finance",
    ("engineering",): "engineering",
    ("company",): "general",
    ("about",): "general",
    ("values",): "general",
    ("communication",): "general",
    ("leadership",): "general",
    ("tools-and-tips",): "general",
}

# Immutable mapping proxy exposed for inspection and cross-module testing
DEPARTMENT_MAPPINGS: Mapping[tuple[str, ...], str] = MappingProxyType(_MAPPING_DATA)

# Pre-sort mappings by tuple length descending once at module load
_SORTED_MAPPINGS: tuple[tuple[tuple[str, ...], str], ...] = tuple(
    sorted(DEPARTMENT_MAPPINGS.items(), key=lambda item: len(item[0]), reverse=True)
)


def department_for(source_path: str) -> str:
    """Resolves the allowed department for a given relative handbook path.

    Args:
        source_path: Forward-slash relative path (e.g. 'people-group/time-off/page.md')

    Returns:
        The department scope name ('people', 'onboarding', 'finance', 'engineering', 'general')

    Raises:
        ValueError: If path is malformed, contains control characters, attempts path traversal,
                    or falls outside allowed handbook folders.
    """
    if not isinstance(source_path, str) or not source_path:
        raise ValueError("Source path must be a non-empty string.")

    # Reject backslashes and leading slashes to enforce forward-slash relative paths
    if "\\" in source_path or source_path.startswith("/"):
        raise ValueError(f"Path must be forward-slash relative: {source_path!r}")

    # Reject control characters or newlines
    if any(ord(char) < 32 or ord(char) == 127 for char in source_path):
        raise ValueError(f"Path contains invalid or control characters: {source_path!r}")

    segments = source_path.split("/")

    # Defend against path traversal, empty segments, dot segments, or trailing slashes
    if ".." in segments or "." in segments or "" in segments:
        raise ValueError(f"Invalid path segments detected in: {source_path!r}")

    # Casefold segments for case-insensitive exclusion checking
    casefolded_segments = tuple(seg.casefold() for seg in segments)

    # Reject explicitly excluded subfolders (case-insensitive)
    for excluded in EXCLUDED_PREFIXES:
        if len(casefolded_segments) >= len(excluded) and casefolded_segments[: len(excluded)] == excluded:
            raise ValueError(f"Path is explicitly excluded from ingestion: {source_path!r}")

    # Match against pre-sorted mappings (case-sensitive)
    tuple_segments = tuple(segments)
    for prefix_segments, department in _SORTED_MAPPINGS:
        if len(tuple_segments) >= len(prefix_segments) and tuple_segments[: len(prefix_segments)] == prefix_segments:
            return department

    raise ValueError(f"Unmapped handbook path: {source_path!r}")