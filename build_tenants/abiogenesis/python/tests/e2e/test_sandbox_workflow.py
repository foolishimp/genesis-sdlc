# Validates: REQ-F-BOOT-001
# Validates: REQ-F-BOOT-002
# Validates: REQ-F-BOOT-003
# Validates: REQ-F-BOOT-004
# Validates: REQ-F-BOOT-005
# Validates: REQ-F-BOOT-006
# Validates: REQ-F-BOOT-007
# Validates: REQ-F-BOOT-008
# Validates: REQ-F-BOOT-009
# Validates: REQ-F-TERRITORY-003
# Validates: REQ-F-CUSTODY-002
# Validates: REQ-F-CMD-001
# Validates: REQ-F-CMD-002
# Validates: REQ-F-CMD-003
# Validates: REQ-F-GATE-001
# Validates: REQ-F-TEST-001
# Validates: REQ-F-UAT-001
# Validates: REQ-F-ASSURE-002
# Validates: REQ-F-CMD-004
# Validates: REQ-F-CTRL-007
# Validates: REQ-F-CTRL-008
# Validates: REQ-F-WORKER-005
"""Sandbox tests for the installed Abiogenesis/Python genesis_sdlc workflow."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from genesis_sdlc.evidence.coverage import assess_module_decomp_artifact
from genesis_sdlc.runtime.backends import load_backend_registry
from genesis_sdlc.runtime.doctor import doctor
from genesis_sdlc.runtime.prompt_view import render_effective_prompt_from_manifest
from genesis_sdlc.runtime.resolve import invoke_worker_turn, load_resolved_runtime, load_worker_registry
from genesis_sdlc.runtime.state import write_session_overrides

from .minimal_project import (
    build_fake_artifact,
    edge_assessments,
    effective_prompt_from_manifest,
    seed_minimal_project_spec,
    write_result_file,
)
from .sandbox_runtime import audit_real_sandbox, install_real_sandbox, reset_runtime_sandbox, run_genesis


@pytest.mark.e2e
@pytest.mark.usecase_id("sandbox_install")
def test_install_bootstraps_real_sandbox_and_gap_scan(run_archive) -> None:
    workspace = run_archive.workspace
    payload = install_real_sandbox(workspace, archive=run_archive)
    run_archive.note("scenario", lane="install", operation="gap_scan")

    assert payload["status"] == "installed"
    assert (workspace / ".genesis" / "genesis.yml").is_file()
    assert (workspace / ".gsdlc" / "release" / "genesis.yml").is_file()
    assert (workspace / ".gsdlc" / "release" / "gtl_spec" / "packages" / "sandbox_project.py").is_file()
    assert (workspace / ".gsdlc" / "release" / "design" / "module_decomp.md").is_file()
    assert (workspace / ".gsdlc" / "release" / "tests").is_dir()
    assert (workspace / ".gsdlc" / "release" / "USER_GUIDE.md").is_file()
    assert (workspace / ".gsdlc" / "release" / "runtime" / "backends.json").is_file()
    assert (workspace / ".gsdlc" / "release" / "runtime" / "adapter-contract.json").is_file()
    assert (workspace / ".gsdlc" / "release" / "runtime" / "workers.json").is_file()
    assert (workspace / ".gsdlc" / "release" / "runtime" / "role-assignments.json").is_file()
    assert (workspace / ".gsdlc" / "release" / "project-templates" / "INTENT_TEMPLATE.md").is_file()
    assert (workspace / ".gsdlc" / "release" / "project-templates" / "build_tenants" / "TENANT_REGISTRY_TEMPLATE.md").is_file()
    assert (workspace / ".gsdlc" / "release" / "project-templates" / "build_tenants" / "common" / "README_TEMPLATE.md").is_file()
    assert (
        workspace / ".gsdlc" / "release" / "project-templates" / "build_tenants" / "common" / "design" / "README_TEMPLATE.md"
    ).is_file()
    assert (workspace / ".gsdlc" / "release" / "project-templates" / "build_tenants" / "variant" / "README_TEMPLATE.md").is_file()
    assert (
        workspace / ".gsdlc" / "release" / "project-templates" / "build_tenants" / "variant" / "design" / "README_TEMPLATE.md"
    ).is_file()
    assert (
        workspace / ".gsdlc" / "release" / "project-templates" / "build_tenants" / "variant" / "design" / "fp" / "README_TEMPLATE.md"
    ).is_file()
    assert (
        workspace / ".gsdlc" / "release" / "project-templates" / "build_tenants" / "variant" / "design" / "fp" / "INTENT_TEMPLATE.md"
    ).is_file()
    assert (
        workspace
        / ".gsdlc"
        / "release"
        / "project-templates"
        / "build_tenants"
        / "variant"
        / "design"
        / "fp"
        / "edge-overrides"
        / "README_TEMPLATE.md"
    ).is_file()
    assert (workspace / ".gsdlc" / "release" / "project-templates" / "docs" / "README_TEMPLATE.md").is_file()
    assert (workspace / ".gsdlc" / "release" / "project-templates" / "requirements" / "README_TEMPLATE.md").is_file()
    assert (
        workspace / ".gsdlc" / "release" / "project-templates" / "requirements" / "STARTER_REQUIREMENTS_TEMPLATE.md"
    ).is_file()
    assert (workspace / "specification" / "INTENT.md").is_file()
    assert (workspace / "specification" / "requirements" / "README.md").is_file()
    assert (workspace / "specification" / "requirements" / "00-starter.md").is_file()
    assert (workspace / "build_tenants" / "TENANT_REGISTRY.md").is_file()
    assert (workspace / "build_tenants" / "common" / "README.md").is_file()
    assert (workspace / "build_tenants" / "common" / "design" / "README.md").is_file()
    assert (workspace / "build_tenants" / "abiogenesis" / "python" / "README.md").is_file()
    assert (workspace / "build_tenants" / "abiogenesis" / "python" / "design" / "README.md").is_file()
    assert (workspace / "build_tenants" / "abiogenesis" / "python" / "design" / "fp" / "README.md").is_file()
    assert (workspace / "build_tenants" / "abiogenesis" / "python" / "design" / "fp" / "INTENT.md").is_file()
    assert (workspace / "build_tenants" / "abiogenesis" / "python" / "design" / "fp" / "edge-overrides" / "README.md").is_file()
    assert (workspace / "docs" / "README.md").is_file()
    assert (workspace / ".ai-workspace" / "runtime" / "resolved-runtime.json").is_file()
    assert not (workspace / "specification" / "design").exists()
    assert not (workspace / "specification" / "standards").exists()
    assert (workspace / ".claude" / "commands" / "gen-start.md").is_file()
    assert (workspace / ".claude" / "commands" / "gen-gaps.md").is_file()
    assert (workspace / ".claude" / "commands" / "gen-status.md").is_file()
    assert (workspace / ".claude" / "commands" / "gen-iterate.md").is_file()
    assert (workspace / ".claude" / "commands" / "gen-review.md").is_file()
    assert (workspace / ".claude" / "commands" / ".genesis-installed").is_file()

    active_workflow = json.loads(
        (workspace / ".gsdlc" / "release" / "active-workflow.json").read_text(encoding="utf-8")
    )
    assert active_workflow["customization"]["requirements_root"] == "specification/requirements"
    assert active_workflow["customization"]["tenant_design_root"] == "build_tenants/abiogenesis/python/design"
    assert active_workflow["customization"]["fp_customization_root"] == "build_tenants/abiogenesis/python/design/fp/edge-overrides"
    assert active_workflow["customization"]["default_worker_assignments"]["constructor"] == "claude_code"
    assert active_workflow["customization"]["default_worker_assignments"]["implementer"] == "claude_code"
    assert ".claude/commands/" in active_workflow["managed_surfaces"]
    assert ".genesis/" in active_workflow["managed_surfaces"]
    assert ".gsdlc/release/" in active_workflow["managed_surfaces"]
    assert "specification/standards/" in active_workflow["territory_boundary"]["authoring_forbidden_on_default_install"]
    assert "build_tenants/" in active_workflow["territory_boundary"]["customization"]
    assert "docs/" in active_workflow["territory_boundary"]["customization"]
    assert ".ai-workspace/runtime/" in active_workflow["territory_boundary"]["runtime_state"]

    resolved_runtime = json.loads(
        (workspace / ".ai-workspace" / "runtime" / "resolved-runtime.json").read_text(encoding="utf-8")
    )
    constructor_assignment = resolved_runtime["role_assignments"]["constructor"]
    assert constructor_assignment["worker_id"] == "claude_code"
    assert constructor_assignment["backend"] == "claude"
    assert constructor_assignment["provenance"]["source_layer"] == "release_declaration"
    implementer_assignment = resolved_runtime["role_assignments"]["implementer"]
    assert implementer_assignment["worker_id"] == "claude_code"
    assert implementer_assignment["backend"] == "claude"
    assert implementer_assignment["provenance"]["source_layer"] == "release_declaration"
    registry = load_backend_registry(workspace)
    assert registry["contract"]["required_methods"] == [
        "probe",
        "invoke",
        "normalize",
        "failure_model",
        "capabilities",
    ]
    worker_registry = load_worker_registry(workspace)
    assert "claude_code" in worker_registry["workers"]
    assert worker_registry["role_assignments"]["constructor"] == "claude_code"
    assert worker_registry["role_assignments"]["implementer"] == "claude_code"

    result = run_genesis(workspace, "gaps", archive=run_archive, label="genesis gaps")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    run_archive.capture_json("gaps_initial.json", data)
    run_archive.update_summary(total_delta=data["total_delta"], converged=data["converged"])

    assert data["jobs_considered"] == 10
    assert data["converged"] is False
    assert data["total_delta"] > 0
    assert data["gaps"][0]["edge"] == "intent→requirements"
    assert "intent_approved" in data["gaps"][0]["failing"]


@pytest.mark.e2e
@pytest.mark.usecase_id("sandbox_install_creates_target")
def test_install_creates_missing_target_directory(run_archive) -> None:
    target = run_archive.run_dir / "fresh_target"
    assert not target.exists()

    payload = install_real_sandbox(target, archive=run_archive)

    assert payload["status"] == "installed"
    assert target.is_dir()
    assert (target / ".genesis" / "genesis.yml").is_file()
    assert (target / ".gsdlc" / "release" / "active-workflow.json").is_file()


@pytest.mark.e2e
@pytest.mark.usecase_id("sandbox_reinstall")
def test_reinstall_preserves_project_authored_spec_surfaces(run_archive) -> None:
    workspace = run_archive.workspace
    install_real_sandbox(workspace, archive=run_archive)

    custom_requirement = workspace / "specification" / "requirements" / "99-local.md"
    custom_requirement.write_text("# Local Requirement\n", encoding="utf-8")
    intent_path = workspace / "specification" / "INTENT.md"
    original_intent = intent_path.read_text(encoding="utf-8")
    intent_path.write_text(original_intent + "\nLOCAL-MARKER\n", encoding="utf-8")

    payload = install_real_sandbox(workspace, archive=run_archive)
    assert payload["status"] == "installed"
    assert custom_requirement.read_text(encoding="utf-8") == "# Local Requirement\n"
    assert "LOCAL-MARKER" in intent_path.read_text(encoding="utf-8")

    audit = audit_real_sandbox(workspace, archive=run_archive)
    assert audit["status"] == "ok"


@pytest.mark.e2e
@pytest.mark.usecase_id("sandbox_self_host_install")
def test_self_host_install_preserves_standards_and_skips_starter_scaffold(run_archive) -> None:
    workspace = run_archive.workspace
    requirements_root = workspace / "specification" / "requirements"
    standards_root = workspace / "specification" / "standards"
    requirements_root.mkdir(parents=True, exist_ok=True)
    standards_root.mkdir(parents=True, exist_ok=True)
    (requirements_root / "README.md").write_text("# Existing Requirements\n", encoding="utf-8")
    (requirements_root / "01-real.md").write_text("# Real Requirement\n", encoding="utf-8")
    (standards_root / "SPEC_METHOD.md").write_text("# Self Host Method\n", encoding="utf-8")

    payload = install_real_sandbox(workspace, slug="self_host_project", self_host=True, archive=run_archive)
    assert payload["status"] == "installed"
    assert payload["install_mode"] == "self_host"

    active_workflow = json.loads(
        (workspace / ".gsdlc" / "release" / "active-workflow.json").read_text(encoding="utf-8")
    )
    assert active_workflow["install_mode"] == "self_host"
    assert active_workflow["territory_boundary"]["authoring_allowed_in_self_host_install"] == [
        "specification/standards/"
    ]
    assert (workspace / "specification" / "standards" / "SPEC_METHOD.md").is_file()
    assert (workspace / "specification" / "requirements" / "01-real.md").is_file()
    assert not (workspace / "specification" / "requirements" / "00-starter.md").exists()

    audit = audit_real_sandbox(workspace, slug="self_host_project", self_host=True, archive=run_archive)
    assert audit["status"] == "ok"
    assert audit["install_mode"] == "self_host"


@pytest.mark.e2e
@pytest.mark.usecase_id("archive_router_provenance")
def test_run_archive_treats_router_worker_as_consistent(run_archive) -> None:
    events_dir = run_archive.workspace / ".ai-workspace" / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    events_path = events_dir / "events.jsonl"
    events_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "event_type": "run_bound",
                        "data": {
                            "edge": "module_decomp→code",
                            "worker_id": "abiogenesis_python_router",
                            "role_id": "implementer",
                            "authority_ref": "runtime://role-dispatch",
                        },
                    }
                ),
                json.dumps(
                    {
                        "event_type": "edge_started",
                        "data": {
                            "edge": "module_decomp→code",
                            "build": "claude_code",
                            "target": "code",
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    run_archive.update_summary(
        selected_assignments={
            "constructor": {"worker_id": "codex", "backend": "codex"},
            "implementer": {"worker_id": "claude_code", "backend": "claude"},
        }
    )

    summary = run_archive._build_summary()

    assert summary["worker_provenance_mode"] == "router_dispatch"
    assert summary["worker_provenance_consistent"] is True
    assert summary["engine_worker_ids"] == ["abiogenesis_python_router"]
    assert summary["engine_build_ids"] == ["claude_code"]
    assert summary["assignment_worker_ids"] == ["claude_code", "codex"]


@pytest.mark.e2e
@pytest.mark.usecase_id("module_decomp_assessment_terms")
def test_module_decomp_assessment_accepts_singular_test_terms(run_archive) -> None:
    artifact = run_archive.workspace / "output" / "module_decomp.md"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(
        """# Module Decomposition

## Modules

- `calculator`
- `test_calculator`
- `test_integration`

## Dependencies

- unit test module depends on calculator
- integration test module depends on calculator

## Build Order

1. calculator
2. test_calculator
3. test_integration
""",
        encoding="utf-8",
    )

    assessments = assess_module_decomp_artifact(artifact)

    assert assessments == [
        {
            "evaluator": "module_schedule",
            "result": "pass",
            "evidence": "module decomposition artifact defines modules, dependencies, and build order.",
        }
    ]


@pytest.mark.e2e
@pytest.mark.usecase_id("sandbox_iterate")
def test_iterate_blocks_on_initial_human_gate(run_archive) -> None:
    workspace = run_archive.workspace
    install_real_sandbox(workspace, archive=run_archive)
    run_archive.note("scenario", lane="iterate", edge="intent→requirements")

    result = run_genesis(workspace, "iterate", archive=run_archive, label="genesis iterate")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    run_archive.capture_json("iterate_initial.json", data)
    run_archive.update_summary(blocking_reason=data.get("blocking_reason"), edge=data.get("edge"))

    assert data["status"] == "iterated"
    assert data["blocking_reason"] == "fh_gate"
    assert data["edge"] == "intent→requirements"
    assert data["fh_gate"]["evaluators"] == ["intent_approved"]


@pytest.mark.e2e
@pytest.mark.usecase_id("sandbox_start_auto")
def test_start_auto_stops_on_first_blocking_human_gate(run_archive) -> None:
    workspace = run_archive.workspace
    install_real_sandbox(workspace, archive=run_archive)
    seed_minimal_project_spec(workspace, archive=run_archive)
    run_archive.note("scenario", lane="start_auto", edge="intent→requirements")

    raised = run_genesis(
        workspace,
        "emit-event",
        "--type",
        "intent_raised",
        "--data",
        json.dumps({"feature": "START-001", "summary": "start auto stop behavior"}),
        archive=run_archive,
        label="emit intent_raised for start auto",
    )
    assert raised.returncode == 0, raised.stderr

    result = run_genesis(workspace, "start", "--auto", archive=run_archive, label="genesis start --auto")
    assert result.returncode == 3, result.stderr
    data = json.loads(result.stdout)
    run_archive.capture_json("start_auto_initial.json", data)

    assert data["status"] == "iterated"
    assert data["edge"] == "intent→requirements"
    assert data["blocking_reason"] == "fh_gate"
    assert data["auto"] is True
    assert data["stopped_by"] == "fh_gate"
    assert data["fh_gate"]["evaluators"] == ["intent_approved"]


@pytest.mark.e2e
@pytest.mark.usecase_id("workflow_fp_dispatch")
def test_workflow_advances_from_fh_gate_to_fp_dispatch(run_archive) -> None:
    workspace = run_archive.workspace
    install_real_sandbox(workspace, archive=run_archive)
    seed_minimal_project_spec(workspace, archive=run_archive)
    run_archive.note("scenario", lane="fp_dispatch", edge="requirements→feature_decomp")

    approve = run_genesis(
        workspace,
        "emit-event",
        "--type",
        "approved",
        "--data",
        json.dumps(
            {
                "kind": "fh_intent",
                "edge": "intent→requirements",
                "actor": "human",
            }
        ),
        archive=run_archive,
        label="emit approved fh_intent",
    )
    assert approve.returncode == 0, approve.stderr

    iterate = run_genesis(workspace, "iterate", archive=run_archive, label="genesis iterate after fh")
    assert iterate.returncode == 0, iterate.stderr
    data = json.loads(iterate.stdout)
    run_archive.capture_json("iterate_after_fh.json", data)

    assert data["status"] == "iterated"
    assert data["blocking_reason"] == "fp_dispatch"
    assert data["edge"] == "requirements→feature_decomp"

    manifest_path = Path(data["fp_manifest_path"])
    assert manifest_path.is_file()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    run_archive.capture_json("fp_manifest_requirements_feature_decomp.json", manifest)
    assert manifest["edge"] == "requirements→feature_decomp"
    assert [item["name"] for item in manifest["failing_evaluators"]] == ["feature_decomp_complete"]

    events_path = workspace / ".ai-workspace" / "events" / "events.jsonl"
    events = [
        json.loads(line)
        for line in events_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    run_bound = next(
        event
        for event in events
        if event["event_type"] == "run_bound" and event["data"].get("edge") == "requirements→feature_decomp"
    )
    assert run_bound["data"]["worker_id"] == "abiogenesis_python_router"
    assert run_bound["data"]["authority_ref"] == "runtime://role-dispatch"

    artifact = build_fake_artifact(manifest["edge"], workspace, manifest)
    run_archive.copy_file(artifact, dest_name=artifact.name)
    result_path = Path(manifest["result_path"])
    write_result_file(
        result_path,
        edge=manifest["edge"],
        actor="sandbox_tester",
        assessments=edge_assessments(manifest["edge"], workspace, manifest),
    )
    run_archive.capture_json("fp_dispatch_result.json", json.loads(result_path.read_text(encoding="utf-8")))

    assessed = run_genesis(
        workspace,
        "assess-result",
        "--result",
        str(result_path),
        archive=run_archive,
        label="genesis assess-result requirements→feature_decomp",
    )
    assert assessed.returncode == 0, assessed.stderr

    gaps = run_genesis(workspace, "gaps", archive=run_archive, label="genesis gaps after fp")
    assert gaps.returncode == 0, gaps.stderr
    gaps_data = json.loads(gaps.stdout)
    run_archive.capture_json("gaps_after_fp.json", gaps_data)
    run_archive.update_summary(total_delta=gaps_data["total_delta"], converged=gaps_data["converged"])
    edge_map = {entry["edge"]: entry for entry in gaps_data["gaps"]}

    assert "feature_decomp_complete" not in edge_map["requirements→feature_decomp"]["failing"]


@pytest.mark.e2e
@pytest.mark.usecase_id("fp_prompt_customization")
def test_installed_fp_prompt_uses_project_local_design_customization(run_archive) -> None:
    workspace = run_archive.workspace
    install_real_sandbox(workspace, archive=run_archive)
    seed_minimal_project_spec(workspace, archive=run_archive)
    run_archive.note("scenario", lane="fp_prompt_customization", edge="requirements→feature_decomp")

    approve = run_genesis(
        workspace,
        "emit-event",
        "--type",
        "approved",
        "--data",
        json.dumps(
            {
                "kind": "fh_intent",
                "edge": "intent→requirements",
                "actor": "human",
            }
        ),
        archive=run_archive,
        label="emit approved fh_intent for prompt customization",
    )
    assert approve.returncode == 0, approve.stderr

    iterate = run_genesis(
        workspace,
        "iterate",
        archive=run_archive,
        label="genesis iterate for prompt customization",
    )
    assert iterate.returncode == 0, iterate.stderr
    payload = json.loads(iterate.stdout)
    assert payload["blocking_reason"] == "fp_dispatch"

    manifest_path = Path(payload["fp_manifest_path"])
    prompt = effective_prompt_from_manifest(manifest_path, workspace=workspace)
    run_archive.capture_text("fp_prompt_customization.txt", prompt)

    assert "Project customization intent:" in prompt
    assert "minimal calculator qualification project" in prompt
    assert "Project requirement refs:" in prompt
    assert "REQ-PROJ-001" in prompt
    assert "Project design refs:" in prompt
    assert "build_tenants/abiogenesis/python/design/README.md" in prompt
    assert "output/feature_decomp.md" in prompt


@pytest.mark.e2e
@pytest.mark.usecase_id("sandbox_reset")
def test_reset_runtime_preserves_installed_surfaces(run_archive) -> None:
    workspace = run_archive.workspace
    install_real_sandbox(workspace, archive=run_archive)
    seed_minimal_project_spec(workspace, archive=run_archive)
    run_archive.note("scenario", lane="reset_runtime")

    _emit_path = workspace / ".ai-workspace" / "fp_results"
    _emit_path.mkdir(parents=True, exist_ok=True)
    (_emit_path / "dummy.json").write_text("{}", encoding="utf-8")
    review_dir = workspace / ".ai-workspace" / "reviews"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "note.md").write_text("review", encoding="utf-8")

    emit = run_genesis(
        workspace,
        "emit-event",
        "--type",
        "intent_raised",
        "--data",
        json.dumps({"feature": "RESET-001", "summary": "runtime reset"}),
        archive=run_archive,
        label="emit intent_raised before reset",
    )
    assert emit.returncode == 0, emit.stderr

    payload = reset_runtime_sandbox(workspace, archive=run_archive)
    run_archive.update_summary(reset_status=payload.get("status"))

    assert payload["status"] == "runtime_reset"
    assert (workspace / ".genesis" / "genesis.yml").is_file()
    assert (workspace / ".gsdlc" / "release" / "active-workflow.json").is_file()
    assert (workspace / ".claude" / "commands" / "gen-start.md").is_file()
    assert (workspace / "specification" / "requirements").is_dir()
    assert not list((workspace / ".ai-workspace" / "events").glob("*"))
    assert not list((workspace / ".ai-workspace" / "fp_results").glob("*"))
    assert not list((workspace / ".ai-workspace" / "reviews").glob("*"))
    assert (workspace / ".ai-workspace" / "runtime").is_dir()
    assert not list((workspace / ".ai-workspace" / "runtime").glob("*"))

    audit = audit_real_sandbox(workspace, archive=run_archive)
    assert audit["status"] == "ok"


@pytest.mark.e2e
@pytest.mark.usecase_id("runtime_invalid_backend")
def test_invalid_runtime_backend_override_fails_at_compile(run_archive) -> None:
    workspace = run_archive.workspace
    install_real_sandbox(workspace, archive=run_archive)
    seed_minimal_project_spec(workspace, archive=run_archive)
    run_archive.note("scenario", lane="runtime_invalid_backend")

    write_session_overrides(workspace, {"worker_assignments": {"constructor": "typo_worker"}})

    with pytest.raises(ValueError, match="not declared"):
        load_resolved_runtime(workspace)


@pytest.mark.e2e
@pytest.mark.usecase_id("runtime_role_assignment")
def test_resolved_runtime_assigns_workers_by_role_and_edge(run_archive) -> None:
    workspace = run_archive.workspace
    install_real_sandbox(workspace, archive=run_archive)
    seed_minimal_project_spec(workspace, archive=run_archive)
    run_archive.note("scenario", lane="runtime_role_assignment")

    write_session_overrides(
        workspace,
        {
            "worker_assignments": {
                "constructor": "claude_code",
                "implementer": "codex",
            }
        },
    )

    resolved_runtime = load_resolved_runtime(workspace)
    run_archive.capture_json("resolved_runtime_role_assignment.json", resolved_runtime)

    constructor_assignment = resolved_runtime["role_assignments"]["constructor"]
    implementer_assignment = resolved_runtime["role_assignments"]["implementer"]
    code_profile = resolved_runtime["edges"]["module_decomp→code"]["profile"]
    design_profile = resolved_runtime["edges"]["feature_decomp→design"]["profile"]

    assert constructor_assignment["worker_id"] == "claude_code"
    assert constructor_assignment["backend"] == "claude"
    assert implementer_assignment["worker_id"] == "codex"
    assert implementer_assignment["backend"] == "codex"
    assert design_profile["role_id"] == "constructor"
    assert design_profile["worker_id"] == "claude_code"
    assert design_profile["backend"] == "claude"
    assert code_profile["role_id"] == "implementer"
    assert code_profile["worker_id"] == "codex"
    assert code_profile["backend"] == "codex"


@pytest.mark.e2e
@pytest.mark.usecase_id("runtime_doctor")
def test_doctor_reports_runtime_misconfiguration_as_structured_findings(run_archive) -> None:
    workspace = run_archive.workspace
    install_real_sandbox(workspace, archive=run_archive)
    seed_minimal_project_spec(workspace, archive=run_archive)
    run_archive.note("scenario", lane="runtime_doctor")

    write_session_overrides(workspace, {"worker_assignments": {"constructor": "typo_worker"}})

    payload = doctor(workspace)
    run_archive.capture_json("doctor_misconfiguration.json", payload)

    assert payload["status"] == "degraded"
    assert payload["resolved_runtime_available"] is False
    assert payload["role_assignments"] == {}
    assert payload["backend_probes"]["claude"]["transport"] == "abg_agent"
    assert any(
        finding["kind"] == "runtime_misconfiguration" and "not declared" in finding["message"]
        for finding in payload["findings"]
    )
    assert (workspace / ".ai-workspace" / "runtime" / "doctor.json").is_file()


@pytest.mark.e2e
@pytest.mark.usecase_id("runtime_adapter_contract")
def test_backend_invocation_returns_normalized_adapter_payload(run_archive, monkeypatch) -> None:
    workspace = run_archive.workspace
    install_real_sandbox(workspace, archive=run_archive)
    run_archive.note("scenario", lane="runtime_adapter_contract", worker="codex", role="constructor")

    class _CompletedProcess:
        returncode = 0
        stdout = "  normalized response  \n"
        stderr = ""

    monkeypatch.setattr("genesis_sdlc.runtime.backends.subprocess.run", lambda *args, **kwargs: _CompletedProcess())

    write_session_overrides(workspace, {"worker_assignments": {"constructor": "codex"}})

    payload = invoke_worker_turn(
        "constructor",
        "Write a normalized response",
        workspace,
        timeout=5,
        workspace_root=workspace,
    )
    run_archive.capture_json("normalized_backend_payload.json", payload)

    assert payload["worker_id"] == "codex"
    assert payload["role_id"] == "constructor"
    assert payload["backend"] == "codex"
    assert payload["content"] == "normalized response"
    assert payload["capabilities"]["full_auto"] is True


@pytest.mark.e2e
@pytest.mark.usecase_id("runtime_prompt_view")
def test_effective_prompt_uses_artifact_override_consistently(run_archive) -> None:
    workspace = run_archive.workspace
    install_real_sandbox(workspace, archive=run_archive)
    seed_minimal_project_spec(workspace, archive=run_archive)
    run_archive.note("scenario", lane="runtime_prompt_view")

    approve = run_genesis(
        workspace,
        "emit-event",
        "--type",
        "approved",
        "--data",
        json.dumps(
            {
                "kind": "fh_intent",
                "edge": "intent→requirements",
                "actor": "human",
            }
        ),
        archive=run_archive,
        label="emit approved fh_intent for prompt view",
    )
    assert approve.returncode == 0, approve.stderr

    iterate = run_genesis(workspace, "iterate", archive=run_archive, label="genesis iterate for prompt view")
    assert iterate.returncode == 0, iterate.stderr
    payload = json.loads(iterate.stdout)
    manifest_path = Path(payload["fp_manifest_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    prompt = render_effective_prompt_from_manifest(
        manifest,
        workspace_root=workspace,
        artifact_override=Path("output/override.md"),
    )
    run_archive.capture_text("prompt_view_override.txt", prompt)

    assert "Write the target artifact to: output/override.md" in prompt
    assert "Suggested output: output/override.md" in prompt
    assert "Context delivery: locator-first" in prompt
    assert "Authoritative context locators:" in prompt
    assert "workspace://specification/requirements/" in prompt
    assert "The project shall provide an `add(a, b)` operation" not in prompt
    assert "# .gsdlc/release/design/README.md" not in prompt


@pytest.mark.e2e
@pytest.mark.usecase_id("runtime_prompt_view_inline_fallback")
def test_effective_prompt_falls_back_to_inline_snapshot_for_non_workspace_worker(monkeypatch, run_archive) -> None:
    manifest = {
        "edge": "requirements→feature_decomp",
        "source_asset": "requirements",
        "failing_evaluators": ["feature_decomp_complete"],
        "delta_summary": "delta = 1 — feature decomposition missing",
        "prompt": "INLINE SNAPSHOT CONTENT",
        "contexts": [
            {
                "name": "requirements_surface",
                "locator": "workspace://specification/requirements/",
                "digest": "sha256:test",
                "content": "INLINE SNAPSHOT CONTENT",
            }
        ],
    }
    monkeypatch.setattr(
        "genesis_sdlc.runtime.prompt_view.load_resolved_runtime",
        lambda _workspace: {
            "role_assignments": {
                "constructor": {
                    "role_id": "constructor",
                    "worker_id": "api_only",
                    "backend": "api",
                    "capabilities": {
                        "interactive_cli": False,
                        "workspace_write": False,
                    },
                }
            },
            "edges": {
                "requirements→feature_decomp": {
                    "profile": {
                        "target_asset": "feature_decomp",
                        "artifact_kind": "feature decomposition",
                        "role_id": "constructor",
                        "worker_id": "api_only",
                        "backend": "api",
                        "authority_contexts": ["requirements_surface"],
                        "suggested_output": "output/feature_decomp.md",
                        "guidance": "Use the inline snapshot.",
                        "customization_intent": "",
                        "requirement_refs": [],
                        "design_refs": [],
                        "required_sections": [],
                    }
                }
            },
        },
    )

    prompt = render_effective_prompt_from_manifest(
        manifest,
        workspace_root=run_archive.workspace,
    )

    assert "Context delivery: inline-snapshot" in prompt
    assert "INLINE SNAPSHOT CONTENT" in prompt
