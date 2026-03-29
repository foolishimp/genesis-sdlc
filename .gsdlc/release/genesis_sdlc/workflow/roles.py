# Implements: REQ-F-GRAPH-003
"""Lightweight workflow role and job manifests for runtime worker assignment."""

from __future__ import annotations


_WORKFLOW_ROLE_MANIFEST: tuple[dict[str, object], ...] = (
    {
        "id": "constructor",
        "name": "constructor",
        "tags": ["f_p", "planning", "design", "tests", "release"],
    },
    {
        "id": "implementer",
        "name": "implementer",
        "tags": ["f_p", "code", "implementation"],
    },
)

_WORKFLOW_JOB_ROLES: dict[str, tuple[str, ...]] = {
    "intent→requirements": (),
    "requirements→feature_decomp": ("constructor",),
    "feature_decomp→design": ("constructor",),
    "design→module_decomp": ("constructor",),
    "module_decomp→code": ("implementer",),
    "module_decomp→unit_tests": ("constructor",),
    "[code, unit_tests]→integration_tests": ("constructor",),
    "[design, integration_tests]→user_guide": ("constructor",),
    "[requirements, design, integration_tests]→bootloader": ("constructor",),
    "[requirements, integration_tests]→uat_tests": (),
}


def workflow_role_manifest() -> list[dict[str, object]]:
    return [
        {
            "id": str(role["id"]),
            "name": str(role["name"]),
            "tags": list(role["tags"]),
        }
        for role in _WORKFLOW_ROLE_MANIFEST
    ]


def workflow_job_roles() -> dict[str, tuple[str, ...]]:
    return dict(_WORKFLOW_JOB_ROLES)
