import pytest

from src.core.config import ROLE_DEPARTMENTS
from src.ingestion.departments import DEPARTMENT_MAPPINGS, department_for


@pytest.mark.parametrize(
    "source_path, expected_dept",
    [
        ("people-group/general-onboarding/index.md", "onboarding"),
        ("people-group/time-off-and-absence/policy.md", "people"),
        ("people-policies/code-of-conduct.md", "people"),
        ("total-rewards/compensation/ranges.md", "people"),
        ("hiring/interviewing.md", "people"),
        ("labor-and-employment-notices/poster.md", "people"),
        ("finance/accounting/process.md", "finance"),
        ("engineering/workflow/git.md", "engineering"),
        ("company/mission.md", "general"),
        ("about/index.md", "general"),
        ("values/culture.md", "general"),
        ("communication/style-guide.md", "general"),
        ("leadership/principles.md", "general"),
        ("tools-and-tips/terminal.md", "general"),
    ],
)
def test_valid_paths_map_to_correct_department(source_path: str, expected_dept: str):
    """Verify that legitimate relative handbook paths map to their designated department."""
    assert department_for(source_path) == expected_dept


@pytest.mark.parametrize(
    "path, expected",
    [
        ("people-group/general-onboardingx/x.md", "people"),  # Near-miss must NOT become onboarding
        ("people-group/general-onboarding", "onboarding"),  # Folder name alone
    ],
)
def test_segment_boundaries(path: str, expected: str):
    """Verify exact segment boundary isolation."""
    assert department_for(path) == expected


@pytest.mark.parametrize(
    "invalid_path",
    [
        "finance/readmes/danielle-ritter.md",  # Excluded personal readmes
        "finance/jihu-support/release-certification.md",  # Excluded software process
        "finance/Readmes/x.md",  # Case-insensitive exclusion check
        "finance/JIHU-SUPPORT/x.md",  # Case-insensitive exclusion check
        "security/guide.md",  # Unmapped handbook section
        "people-group/../security/guide.md",  # Path traversal attempt
        "people-groupx/test.md",  # Partial segment match attempt
        "People-Group/index.md",  # Incorrect casing (fail closed)
        "/people-group/index.md",  # Leading slash (absolute path)
        "C:/people-group/index.md",  # Windows absolute path
        "people-group\\index.md",  # Backslash separator
        "people-group//x.md",  # Empty segment
        "people-group/./x.md",  # Dot segment
        "people-group/x.md/",  # Trailing slash
        "people-group/x.md\n",  # Control character / newline
        "",  # Empty path
        None,  # Non-string input
    ],
)
def test_invalid_or_excluded_paths_raise_value_error(invalid_path: str):
    """Verify that unmapped, excluded, or maliciously formatted paths fail closed."""
    with pytest.raises(ValueError):
        department_for(invalid_path)  # type: ignore[arg-type]


def test_every_mapped_department_exists_in_access_table():
    """Cross-validate that every department in ingestion mappings exists in the RBAC config table."""
    known_departments = {dept for allowed_set in ROLE_DEPARTMENTS.values() for dept in allowed_set}
    mapped_departments = set(DEPARTMENT_MAPPINGS.values())
    assert mapped_departments <= known_departments