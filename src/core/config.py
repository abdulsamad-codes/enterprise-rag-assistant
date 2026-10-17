from collections.abc import Mapping
from types import MappingProxyType

ROLE_DEPARTMENTS: Mapping[str, frozenset[str]] = MappingProxyType({
    # Keep every role's access policy in one source-of-truth table.
    "new_hire": frozenset({"onboarding", "general"}),
    "hr": frozenset({"people", "onboarding", "general"}),
    "finance": frozenset({"finance", "onboarding", "general"}),
    "engineer": frozenset({"engineering", "onboarding", "general"}),
})

# Derive valid labels from the access table so a second department list cannot drift.
KNOWN_DEPARTMENTS = frozenset({
    department
    for departments in ROLE_DEPARTMENTS.values()
    for department in departments
})


def allowed_departments(role: object) -> frozenset[str]:
    # Reject missing, non-string, wrongly formatted, and unknown roles before lookup.
    if not isinstance(role, str) or role not in ROLE_DEPARTMENTS:
        raise ValueError(f"Unknown role: {role!r}")

    # Return the immutable policy value so callers cannot change the shared table.
    return ROLE_DEPARTMENTS[role]
