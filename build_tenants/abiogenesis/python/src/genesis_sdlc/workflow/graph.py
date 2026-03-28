# Implements: REQ-F-GRAPH-001
# Implements: REQ-F-CMD-001
# Implements: REQ-F-GATE-001
# Implements: REQ-F-DOCS-002
# Implements: REQ-F-UAT-002
# Implements: REQ-F-UAT-003
# Implements: REQ-F-BOOTDOC-001
"""GTL graph, jobs, roles, operators, and evaluators for genesis_sdlc."""

from __future__ import annotations

from gtl.algebra import deferred_refinement
from gtl.graph import Graph, GraphVector
from gtl.operator_model import Evaluator, F_D, F_H, F_P, Operator, Rule
from gtl.work_model import ContractRef, Job, Role

from .assets import (
    BASE_CONTEXTS,
    BOOTLOADER_CONTEXTS,
    DESIGN_CONTEXTS,
    FEATURE_CONTEXTS,
    BASE_NODES,
    RELEASE_CONTEXTS,
    bootloader,
    code,
    design,
    feature_decomp,
    integration_tests,
    intent,
    module_decomp,
    requirements,
    uat_tests,
    unit_tests,
    user_guide,
)


python_constructor = Operator("python_constructor", F_P, "agent://genesis_sdlc/python")
human_gate = Operator("human_gate", F_H, "fh://single")
deterministic_check = Operator("deterministic_check", F_D, "")

standard_gate = Rule(
    name="standard_gate",
    kind="gate",
    config={"approve": {"kind": "consensus", "n": 1, "m": 1}, "dissent": "recorded"},
)


eval_intent_fh = Evaluator(
    "intent_approved",
    F_H,
    "Human confirms intent is clear, bounded, and worth realizing.",
)
eval_feature_fd = Evaluator(
    "requirements_loaded",
    F_D,
    "The live requirement surface is readable and key discovery is deterministic.",
    binding=(
        "exec://python -m genesis_sdlc.evidence.fd_checks requirements_loaded "
        "--package-ref genesis_sdlc.workflow:package "
        "--active-workflow-path .gsdlc/release/active-workflow.json"
    ),
)
eval_feature_fp = Evaluator(
    "feature_decomp_complete",
    F_P,
    "Feature decomposition covers the requirement surface and preserves dependency order.",
)
eval_design_fp = Evaluator(
    "design_complete",
    F_P,
    "Design specifies interfaces, module boundaries, and realization constraints.",
)
eval_design_fh = Evaluator(
    "design_approved",
    F_H,
    "Human approves the design before module scheduling and construction proceed.",
)
eval_module_fd = Evaluator(
    "module_coverage",
    F_D,
    "Every feature stem appears in the module schedule and dependency DAG is acyclic.",
    binding=(
        "exec://python -m genesis_sdlc.evidence.fd_checks module_coverage "
        "--modules-root build_tenants/abiogenesis/python/design/modules"
    ),
)
eval_module_fp = Evaluator(
    "module_schedule",
    F_P,
    "Module decomposition yields clean module boundaries, interfaces, and rank order.",
)
eval_module_fh = Evaluator(
    "schedule_approved",
    F_H,
    "Human approves the module schedule before code or test construction begins.",
)
eval_code_fd = Evaluator(
    "impl_tags",
    F_D,
    "All source files carry Implements traceability tags for the active requirement surface.",
    binding=(
        "exec://python -m genesis_sdlc.evidence.fd_checks implements_tags "
        "--path build_tenants/abiogenesis/python/src"
    ),
)
eval_code_fp = Evaluator(
    "code_complete",
    F_P,
    "Source implementation satisfies the approved module schedule.",
)
eval_unit_fd = Evaluator(
    "test_tags",
    F_D,
    "All unit-test files carry Validates traceability tags for the active requirement surface.",
    binding=(
        "exec://python -m genesis_sdlc.evidence.fd_checks validates_tags "
        "--path build_tenants/abiogenesis/python/tests"
    ),
)
eval_unit_fp = Evaluator(
    "unit_test_surface_complete",
    F_P,
    "Unit tests cover the module interfaces and deterministic invariants implied by the schedule.",
)
eval_integration_fd = Evaluator(
    "e2e_tests_exist",
    F_D,
    "At least one e2e scenario exists for the integrated workflow surface.",
    binding=(
        "exec://python -m genesis_sdlc.evidence.fd_checks e2e_tests_exist "
        "--path build_tenants/abiogenesis/python/tests"
    ),
)
eval_integration_fd_report = Evaluator(
    "sandbox_report_exists",
    F_D,
    "Structured sandbox report exists and records all_pass: true.",
    binding=(
        "exec://python -m genesis_sdlc.evidence.fd_checks sandbox_report_exists "
        "--path .ai-workspace/uat/sandbox_report.json"
    ),
)
eval_integration_fp = Evaluator(
    "coverage_complete",
    F_P,
    "Integration and E2E evidence cover the operator-facing requirement surface.",
)
eval_integration_fp_sandbox = Evaluator(
    "sandbox_e2e_passed",
    F_P,
    "Sandbox install and e2e execution produce a passing structured report.",
)
eval_guide_fd = Evaluator(
    "guide_version_current",
    F_D,
    "The user guide is version-current and tags the active requirement surface.",
    binding=(
        "exec://python -m genesis_sdlc.evidence.fd_checks guide_version_current "
        "--guide-path build_tenants/abiogenesis/python/release/USER_GUIDE.md "
        "--version-path .gsdlc/release/active-workflow.json"
    ),
)
eval_guide_fd_coverage = Evaluator(
    "guide_req_coverage",
    F_D,
    "The user guide carries the active requirement keys as traceability tags.",
    binding=(
        "exec://python -m genesis_sdlc.evidence.fd_checks guide_req_coverage "
        "--guide-path build_tenants/abiogenesis/python/release/USER_GUIDE.md "
        "--package-ref genesis_sdlc.workflow:package "
        "--active-workflow-path .gsdlc/release/active-workflow.json"
    ),
)
eval_guide_fp = Evaluator(
    "guide_content_certified",
    F_P,
    "The user guide explains install, first session, operating loop, and recovery paths.",
)
eval_bootloader_fd_1 = Evaluator(
    "spec_hash_current",
    F_D,
    "The compiled bootloader hash matches the active requirement surface.",
    binding=(
        "exec://python -m genesis_sdlc.evidence.fd_checks spec_hash_current "
        "--package-ref genesis_sdlc.workflow:package "
        "--active-workflow-path .gsdlc/release/active-workflow.json "
        "--bootloader-path build_tenants/abiogenesis/python/release/SDLC_BOOTLOADER.md"
    ),
)
eval_bootloader_fd_2 = Evaluator(
    "version_current",
    F_D,
    "The compiled bootloader version matches the active workflow version.",
    binding=(
        "exec://python -m genesis_sdlc.evidence.fd_checks version_current "
        "--bootloader-path build_tenants/abiogenesis/python/release/SDLC_BOOTLOADER.md "
        "--version-path .gsdlc/release/active-workflow.json"
    ),
)
eval_bootloader_fd_3 = Evaluator(
    "section_coverage_complete",
    F_D,
    "The compiled bootloader contains the mandatory sections.",
    binding=(
        "exec://python -m genesis_sdlc.evidence.fd_checks section_coverage_complete "
        "--bootloader-path build_tenants/abiogenesis/python/release/SDLC_BOOTLOADER.md"
    ),
)
eval_bootloader_fd_4 = Evaluator(
    "references_valid",
    F_D,
    "All workspace references emitted into the bootloader resolve.",
    binding=(
        "exec://python -m genesis_sdlc.evidence.fd_checks references_valid "
        "--bootloader-path build_tenants/abiogenesis/python/release/SDLC_BOOTLOADER.md"
    ),
)
eval_bootloader_fp = Evaluator(
    "synthesize_bootloader",
    F_P,
    "The bootloader is compiled from specification, standards, and design surfaces.",
)
eval_bootloader_fh = Evaluator(
    "bootloader_approved",
    F_H,
    "Human approves the compiled bootloader before it is treated as operative.",
)
eval_uat_fh = Evaluator(
    "uat_accepted",
    F_H,
    "Human accepts the release against requirements using sandbox and documentation evidence.",
)


v_intent_requirements = GraphVector(
    name="intent→requirements",
    source=intent,
    target=requirements,
    operators=(human_gate,),
    evaluators=(eval_intent_fh,),
    contexts=FEATURE_CONTEXTS,
    rule=standard_gate,
)
v_requirements_feature_decomp = GraphVector(
    name="requirements→feature_decomp",
    source=requirements,
    target=feature_decomp,
    operators=(python_constructor, deterministic_check),
    evaluators=(eval_feature_fd, eval_feature_fp),
    contexts=FEATURE_CONTEXTS,
)
v_feature_decomp_design = GraphVector(
    name="feature_decomp→design",
    source=feature_decomp,
    target=design,
    operators=(python_constructor, human_gate),
    evaluators=(eval_design_fp, eval_design_fh),
    contexts=DESIGN_CONTEXTS,
    rule=standard_gate,
)
v_design_module_decomp = GraphVector(
    name="design→module_decomp",
    source=design,
    target=module_decomp,
    operators=(python_constructor, human_gate, deterministic_check),
    evaluators=(eval_module_fd, eval_module_fp, eval_module_fh),
    contexts=DESIGN_CONTEXTS,
    rule=standard_gate,
)
v_module_decomp_code = GraphVector(
    name="module_decomp→code",
    source=module_decomp,
    target=code,
    operators=(python_constructor, deterministic_check),
    evaluators=(eval_code_fd, eval_code_fp),
    contexts=DESIGN_CONTEXTS,
)
v_module_decomp_unit_tests = GraphVector(
    name="module_decomp→unit_tests",
    source=module_decomp,
    target=unit_tests,
    operators=(python_constructor, deterministic_check),
    evaluators=(eval_unit_fd, eval_unit_fp),
    contexts=DESIGN_CONTEXTS,
)
v_integration_tests = GraphVector(
    name="[code, unit_tests]→integration_tests",
    source=(code, unit_tests),
    target=integration_tests,
    operators=(python_constructor, deterministic_check),
    evaluators=(
        eval_integration_fd,
        eval_integration_fd_report,
        eval_integration_fp,
        eval_integration_fp_sandbox,
    ),
    contexts=DESIGN_CONTEXTS,
)
v_user_guide = GraphVector(
    name="[design, integration_tests]→user_guide",
    source=(design, integration_tests),
    target=user_guide,
    operators=(python_constructor, deterministic_check),
    evaluators=(eval_guide_fd, eval_guide_fd_coverage, eval_guide_fp),
    contexts=RELEASE_CONTEXTS,
)
v_bootloader = GraphVector(
    name="[requirements, design, integration_tests]→bootloader",
    source=(requirements, design, integration_tests),
    target=bootloader,
    operators=(python_constructor, deterministic_check, human_gate),
    evaluators=(
        eval_bootloader_fd_1,
        eval_bootloader_fd_2,
        eval_bootloader_fd_3,
        eval_bootloader_fd_4,
        eval_bootloader_fp,
        eval_bootloader_fh,
    ),
    contexts=BOOTLOADER_CONTEXTS,
    rule=standard_gate,
)
v_uat_tests = GraphVector(
    name="[requirements, integration_tests]→uat_tests",
    source=(requirements, integration_tests),
    target=uat_tests,
    operators=(human_gate,),
    evaluators=(eval_uat_fh,),
    contexts=RELEASE_CONTEXTS,
    rule=standard_gate,
)


BASE_VECTORS = (
    v_intent_requirements,
    v_requirements_feature_decomp,
    v_feature_decomp_design,
    v_design_module_decomp,
    v_module_decomp_code,
    v_module_decomp_unit_tests,
    v_integration_tests,
    v_user_guide,
    v_bootloader,
    v_uat_tests,
)

role_constructor = Role(name="constructor", tags=("f_p", "python"))

job_intent_requirements = Job(
    name="intent→requirements",
    contracts=(ContractRef(kind="graph_vector", target_id=v_intent_requirements.id),),
    roles=(),
)
job_requirements_feature_decomp = Job(
    name="requirements→feature_decomp",
    contracts=(ContractRef(kind="graph_vector", target_id=v_requirements_feature_decomp.id),),
    roles=(role_constructor,),
)
job_feature_decomp_design = Job(
    name="feature_decomp→design",
    contracts=(ContractRef(kind="graph_vector", target_id=v_feature_decomp_design.id),),
    roles=(role_constructor,),
)
job_design_module_decomp = Job(
    name="design→module_decomp",
    contracts=(ContractRef(kind="graph_vector", target_id=v_design_module_decomp.id),),
    roles=(role_constructor,),
)
job_module_decomp_code = Job(
    name="module_decomp→code",
    contracts=(ContractRef(kind="graph_vector", target_id=v_module_decomp_code.id),),
    roles=(role_constructor,),
)
job_module_decomp_unit_tests = Job(
    name="module_decomp→unit_tests",
    contracts=(ContractRef(kind="graph_vector", target_id=v_module_decomp_unit_tests.id),),
    roles=(role_constructor,),
)
job_integration_tests = Job(
    name="[code, unit_tests]→integration_tests",
    contracts=(ContractRef(kind="graph_vector", target_id=v_integration_tests.id),),
    roles=(role_constructor,),
)
job_user_guide = Job(
    name="[design, integration_tests]→user_guide",
    contracts=(ContractRef(kind="graph_vector", target_id=v_user_guide.id),),
    roles=(role_constructor,),
)
job_bootloader = Job(
    name="[requirements, design, integration_tests]→bootloader",
    contracts=(ContractRef(kind="graph_vector", target_id=v_bootloader.id),),
    roles=(role_constructor,),
)
job_uat_tests = Job(
    name="[requirements, integration_tests]→uat_tests",
    contracts=(ContractRef(kind="graph_vector", target_id=v_uat_tests.id),),
    roles=(),
)


BASE_JOBS = (
    job_intent_requirements,
    job_requirements_feature_decomp,
    job_feature_decomp_design,
    job_design_module_decomp,
    job_module_decomp_code,
    job_module_decomp_unit_tests,
    job_integration_tests,
    job_user_guide,
    job_bootloader,
    job_uat_tests,
)

BASE_OPERATORS = (
    python_constructor,
    human_gate,
    deterministic_check,
)

BASE_EVALUATORS = (
    eval_intent_fh,
    eval_feature_fd,
    eval_feature_fp,
    eval_design_fp,
    eval_design_fh,
    eval_module_fd,
    eval_module_fp,
    eval_module_fh,
    eval_code_fd,
    eval_code_fp,
    eval_unit_fd,
    eval_unit_fp,
    eval_integration_fd,
    eval_integration_fd_report,
    eval_integration_fp,
    eval_integration_fp_sandbox,
    eval_guide_fd,
    eval_guide_fd_coverage,
    eval_guide_fp,
    eval_bootloader_fd_1,
    eval_bootloader_fd_2,
    eval_bootloader_fd_3,
    eval_bootloader_fd_4,
    eval_bootloader_fp,
    eval_bootloader_fh,
    eval_uat_fh,
)

BASE_RULES = (standard_gate,)
BASE_ROLES = (role_constructor,)
BASE_REFINEMENT_BOUNDARIES = tuple(
    deferred_refinement(
        vector.name,
        inputs=vector.source if isinstance(vector.source, tuple) else (vector.source,),
        outputs=(vector.target,),
    )
    for vector in BASE_VECTORS
)

workflow_graph = Graph(
    name="genesis_sdlc_base_process_workflow",
    inputs=(intent,),
    outputs=(uat_tests, user_guide, bootloader),
    nodes=BASE_NODES,
    vectors=BASE_VECTORS,
    contexts=(),
    rules=BASE_RULES,
    tags=("genesis_sdlc", "base_process_workflow"),
)
