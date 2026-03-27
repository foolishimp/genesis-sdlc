# Implements: REQ-F-GRAPH-001
# Implements: REQ-F-GRAPH-002
"""Typed lifecycle assets and shared contexts for the workflow declaration."""

from __future__ import annotations

from gtl.graph import Context, Node


PENDING_DIGEST = "sha256:" + ("0" * 64)


def _workspace_context(name: str, locator: str) -> Context:
    return Context(name=name, locator=f"workspace://{locator}", digest=PENDING_DIGEST)


requirements_context = _workspace_context("requirements_surface", "specification/requirements/")
standards_context = _workspace_context("standards_surface", "specification/standards/")
design_context = _workspace_context(
    "python_design_surface",
    "build_tenants/abiogenesis/python/design/",
)


intent = Node(
    name="intent",
    schema="IntentDoc",
    markov=("problem_stated", "value_proposition_clear", "scope_bounded"),
)
requirements = Node(
    name="requirements",
    schema="RequirementFamilySet",
    markov=("requirements_loaded", "keys_testable", "method_aligned"),
)
feature_decomp = Node(
    name="feature_decomp",
    schema="FeatureSet",
    markov=("feature_surface_complete", "feature_dependencies_declared", "coverage_mapped"),
)
design = Node(
    name="design",
    schema="DesignSet",
    markov=("interfaces_declared", "module_inputs_clear", "traceable_to_requirements"),
)
module_decomp = Node(
    name="module_decomp",
    schema="ModuleSchedule",
    markov=("module_schedule_defined", "dependency_dag_acyclic", "feature_assignment_complete"),
)
code = Node(
    name="code",
    schema="SourceSet",
    markov=("source_materialized", "implements_tags_present", "module_interfaces_satisfied"),
)
unit_tests = Node(
    name="unit_tests",
    schema="TestSet",
    markov=("test_surfaces_materialized", "validates_tags_present", "module_edges_covered"),
)
integration_tests = Node(
    name="integration_tests",
    schema="IntegrationEvidence",
    markov=("integration_cycle_defined", "sandbox_evidence_ready", "coverage_assessed"),
)
user_guide = Node(
    name="user_guide",
    schema="OperatorGuide",
    markov=("guide_version_current", "guide_req_coverage", "operating_loop_documented"),
)
bootloader = Node(
    name="bootloader",
    schema="BootloaderDoc",
    markov=("spec_hash_current", "version_current", "section_coverage_complete", "references_valid"),
)
uat_tests = Node(
    name="uat_tests",
    schema="AcceptanceDecision",
    markov=("sandbox_report_available", "acceptance_decided"),
)


BASE_NODES = (
    intent,
    requirements,
    feature_decomp,
    design,
    module_decomp,
    code,
    unit_tests,
    integration_tests,
    user_guide,
    bootloader,
    uat_tests,
)

BASE_CONTEXTS = (
    requirements_context,
    standards_context,
    design_context,
)

FEATURE_CONTEXTS = (requirements_context,)
DESIGN_CONTEXTS = (requirements_context, design_context)
RELEASE_CONTEXTS = (requirements_context, design_context, standards_context)
