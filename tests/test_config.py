import pytest

from src.core.config import KNOWN_DEPARTMENTS, ROLE_DEPARTMENTS, allowed_departments


def test_known_departments_contains_exactly_the_supported_departments():
    # Keep the shared validation set complete and immutable for every ingestion caller.
    assert KNOWN_DEPARTMENTS == {"onboarding", "general", "people", "finance", "engineering"}
    assert isinstance(KNOWN_DEPARTMENTS, frozenset)


@pytest.mark.parametrize(
    "role, expected",
    [
        ("new_hire", frozenset({"onboarding", "general"})),
        ("hr", frozenset({"people", "onboarding", "general"})),
        ("finance", frozenset({"finance", "onboarding", "general"})),
        ("engineer", frozenset({"engineering", "onboarding", "general"})),
    ],
)
def test_each_role_gets_exactly_allowed_departments(role, expected):
    assert allowed_departments(role) == expected


def test_engineer_cannot_access_restricted_departments():
    departments = allowed_departments("engineer")

    assert "finance" not in departments
    assert "people" not in departments


def test_unknown_role_raises_value_error():
    with pytest.raises(ValueError):
        allowed_departments("intern")


@pytest.mark.parametrize("role", ["", "HR", " hr", None, "admin"])
def test_invalid_roles_raise_value_error(role):
    with pytest.raises(ValueError):
        allowed_departments(role)


def test_allowed_departments_returns_frozenset():
    assert isinstance(allowed_departments("hr"), frozenset)


def test_role_departments_table_is_read_only():
    with pytest.raises(TypeError):
        ROLE_DEPARTMENTS["intern"] = frozenset({"finance"})
