# Validates: REQ-F-CMD-001
# Validates: REQ-F-TEST-001
# Validates: REQ-F-TEST-004
# Validates: REQ-F-TEST-005
# Validates: REQ-F-MVP-003
# Validates: REQ-F-ASSURE-002
"""Live qualification lane for sandbox-backed workflow scenarios."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from genesis_sdlc.evidence.uat import write_sandbox_report
from genesis_sdlc.runtime.resolve import load_resolved_runtime, load_worker_registry
from genesis_sdlc.runtime.state import write_session_overrides

from .live_transport import call_agent, roles_ready, selected_assignment
from .minimal_project import (
    BOOTLOADER_ARTIFACT,
    BOOTLOADER_EDGE,
    DOWNSTREAM_RELEASE_EDGES,
    INTEGRATION_EDGE,
    UAT_EDGE,
    USER_GUIDE_EDGE,
    build_fake_artifact,
    constructive_prompt,
    default_archive_name,
    edge_artifact,
    edge_assessments,
    fd_repair_prompt,
    seed_minimal_project_spec,
    write_result_file,
)
from .sandbox_runtime import install_real_sandbox, run_genesis


pytestmark = [pytest.mark.e2e, pytest.mark.live_fp]


def _configured_live_workers(
    workspace: Path,
    *,
    overrides: dict[str, str] | None = None,
) -> dict[str, dict[str, str]]:
    explicit_overrides = overrides
    if explicit_overrides is None:
        override = os.environ.get("GSDLC_LIVE_AGENT")
        if override:
            registry = load_worker_registry(workspace)
            role_defaults = registry.get("role_assignments", {})
            if not isinstance(role_defaults, dict):
                raise ValueError("worker registry role_assignments must be an object")
            explicit_overrides = {
                str(role_id): override
                for role_id in role_defaults
                if isinstance(role_id, str) and role_id
            }
    if explicit_overrides:
        registry = load_worker_registry(workspace)
        role_defaults = registry.get("role_assignments", {})
        if not isinstance(role_defaults, dict):
            raise ValueError("worker registry role_assignments must be an object")
        write_session_overrides(
            workspace,
            {
                "worker_assignments": {
                    str(role_id): str(worker_id)
                    for role_id, worker_id in explicit_overrides.items()
                    if isinstance(role_id, str) and role_id and isinstance(worker_id, str) and worker_id
                }
            },
        )
    resolved = load_resolved_runtime(workspace)
    assignments = resolved.get("role_assignments", {})
    if not isinstance(assignments, dict):
        raise ValueError("resolved runtime role_assignments must be an object")
    configured: dict[str, dict[str, str]] = {}
    for role_id, assignment in assignments.items():
        if not isinstance(assignment, dict):
            raise ValueError(f"resolved runtime assignment for role {role_id!r} must be an object")
        worker_id = assignment.get("worker_id")
        backend = assignment.get("backend")
        if not isinstance(worker_id, str) or not worker_id:
            raise ValueError(f"resolved runtime worker assignment for role {role_id!r} declares no worker")
        if not isinstance(backend, str) or not backend:
            raise ValueError(f"resolved runtime worker assignment for role {role_id!r} declares no backend")
        configured[str(role_id)] = {
            "role_id": str(role_id),
            "worker_id": worker_id,
            "backend": backend,
        }
    return configured


def _require_live_workers(
    workspace: Path,
    *,
    overrides: dict[str, str] | None = None,
) -> dict[str, dict[str, str]]:
    if os.environ.get("CODEX_LIVE_FP") != "1":
        pytest.skip("set CODEX_LIVE_FP=1 to enable live qualification")
    configured = _configured_live_workers(workspace, overrides=overrides)
    available, unavailable = roles_ready(workspace)
    if not available:
        unavailable_text = ", ".join(
            f"{role}={assignment.get('worker_id')} via {assignment.get('backend')}"
            for role, assignment in sorted(unavailable.items())
        )
        pytest.skip(f"selected live worker assignments are unavailable: {unavailable_text}")
    return configured


def _assignment_for_edge(workspace: Path, edge: str) -> dict[str, str]:
    assignment = selected_assignment(workspace, edge=edge)
    return {
        "role_id": str(assignment["role_id"]),
        "worker_id": str(assignment["worker_id"]),
        "backend": str(assignment["backend"]),
    }

def _word_count(text: str) -> int:
    return len(text.split())


def _safe_stem(edge: str) -> str:
    return edge.replace("→", "_").replace("[", "").replace("]", "").replace(", ", "_").replace(" ", "")


def _edge_timeout(edge: str) -> int:
    return 600 if edge == BOOTLOADER_EDGE else 360


def _run_json(workspace: Path, *args: str, archive=None, label: str | None = None) -> dict:
    result = run_genesis(workspace, *args, archive=archive, label=label)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _emit_event(workspace: Path, event_type: str, data: dict, *, archive=None, label: str | None = None) -> None:
    result = run_genesis(
        workspace,
        "emit-event",
        "--type",
        event_type,
        "--data",
        json.dumps(data),
        archive=archive,
        label=label or f"emit {event_type}",
    )
    assert result.returncode == 0, result.stderr


def _qualify_live_edge(workspace: Path, manifest: dict, *, archive) -> None:
    edge = manifest["edge"]
    assignment = _assignment_for_edge(workspace, edge)
    relative_artifact = edge_artifact(edge)
    if relative_artifact is None:
        raise KeyError(f"no live artifact target declared for edge: {edge}")

    prompt = constructive_prompt(edge, manifest, workspace=workspace, artifact_path=relative_artifact)
    artifact = workspace / relative_artifact
    artifact.parent.mkdir(parents=True, exist_ok=True)

    safe_stem = _safe_stem(edge)
    archive.capture_text(f"{safe_stem}_prompt.txt", prompt)
    archive.capture_json(f"{safe_stem}_manifest.json", manifest)
    archive.update_summary(
        prompt_words=_word_count(prompt),
        selected_role=assignment["role_id"],
        selected_worker=assignment["worker_id"],
        selected_backend=assignment["backend"],
    )

    backend_result = call_agent(prompt, str(workspace), role=assignment["role_id"], timeout=_edge_timeout(edge))
    archive.capture_json(f"{safe_stem}_backend_result.json", backend_result)
    archive.capture_text(f"{safe_stem}_raw_response.txt", str(backend_result["content"]))

    if edge == INTEGRATION_EDGE:
        write_sandbox_report(
            workspace / ".ai-workspace" / "uat" / "sandbox_report.json",
            scenario="live_qualification",
            sandbox_path=str(workspace),
        )

    archive.copy_file(artifact, dest_name=default_archive_name(edge))

    result_path = Path(manifest["result_path"])
    write_result_file(
        result_path,
        edge=edge,
        actor=f"live_{safe_stem}_judge",
        assessments=edge_assessments(edge, workspace, manifest),
    )
    archive.capture_json(f"{safe_stem}_result.json", json.loads(result_path.read_text(encoding="utf-8")))

    assess = run_genesis(
        workspace,
        "assess-result",
        "--result",
        str(result_path),
        archive=archive,
        label=f"genesis assess-result {edge}",
    )
    assert assess.returncode == 0, assess.stderr


def _repair_live_fd_gap(workspace: Path, edge: str, *, archive) -> None:
    assignment = _assignment_for_edge(workspace, edge)
    relative_artifact = edge_artifact(edge)
    if relative_artifact is None:
        raise KeyError(f"no repair artifact declared for edge: {edge}")

    prompt = fd_repair_prompt(edge, workspace)
    artifact = workspace / relative_artifact
    artifact.parent.mkdir(parents=True, exist_ok=True)

    safe_stem = _safe_stem(f"{edge}_repair")
    archive.capture_text(f"{safe_stem}_prompt.txt", prompt)
    backend_result = call_agent(prompt, str(workspace), role=assignment["role_id"], timeout=_edge_timeout(edge))
    archive.capture_json(f"{safe_stem}_backend_result.json", backend_result)
    archive.capture_text(f"{safe_stem}_raw_response.txt", str(backend_result["content"]))

    archive.copy_file(artifact, dest_name=f"repair_{artifact.name}")


def _qualify_fake_edge(workspace: Path, manifest: dict, *, archive) -> None:
    edge = manifest["edge"]
    artifact = build_fake_artifact(edge, workspace, manifest)
    archive.copy_file(artifact, dest_name=default_archive_name(edge))
    result_path = Path(manifest["result_path"])
    write_result_file(
        result_path,
        edge=edge,
        actor="focused_fake_qualifier",
        assessments=edge_assessments(edge, workspace, manifest),
    )
    archive.capture_json(
        f"{_safe_stem(edge)}_fake_result.json",
        json.loads(result_path.read_text(encoding="utf-8")),
    )
    assess = run_genesis(
        workspace,
        "assess-result",
        "--result",
        str(result_path),
        archive=archive,
        label=f"genesis assess-result {edge}",
    )
    assert assess.returncode == 0, assess.stderr


@pytest.mark.usecase_id("workflow_fp_dispatch")
def test_workflow_advances_from_fh_gate_to_live_fp_qualification(run_archive) -> None:
    workspace = run_archive.workspace
    install_real_sandbox(workspace, archive=run_archive)
    seed_minimal_project_spec(workspace, archive=run_archive)
    assignments = _require_live_workers(workspace)
    run_archive.update_summary(selected_assignments=assignments)
    run_archive.note(
        "scenario",
        lane="live",
        edge="requirements→feature_decomp",
        assignments=assignments,
    )

    _emit_event(
        workspace,
        "approved",
        {
            "kind": "fh_intent",
            "edge": "intent→requirements",
            "actor": "human",
        },
        archive=run_archive,
        label="emit approved fh_intent",
    )

    iterate = _run_json(workspace, "iterate", archive=run_archive, label="genesis iterate live")
    run_archive.capture_json("iterate_live_fp.json", iterate)

    assert iterate["blocking_reason"] == "fp_dispatch"
    assert iterate["edge"] == "requirements→feature_decomp"

    manifest_path = Path(iterate["fp_manifest_path"])
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assignment = _assignment_for_edge(workspace, manifest["edge"])
    run_archive.capture_json("fp_live_manifest.json", manifest)
    run_archive.update_summary(
        lane="live",
        edge=manifest["edge"],
        manifest_id=manifest["manifest_id"],
        result_path=manifest["result_path"],
        selected_role=assignment["role_id"],
        selected_worker=assignment["worker_id"],
        selected_backend=assignment["backend"],
    )

    _qualify_live_edge(workspace, manifest, archive=run_archive)

    gaps = _run_json(workspace, "gaps", archive=run_archive, label="genesis gaps after live fp")
    run_archive.capture_json("gaps_after_live_fp.json", gaps)
    edge_map = {entry["edge"]: entry for entry in gaps["gaps"]}
    run_archive.update_summary(total_delta=gaps["total_delta"], converged=gaps["converged"])

    assert "feature_decomp_complete" not in edge_map["requirements→feature_decomp"]["failing"]


@pytest.mark.usecase_id("gsdlc_steel_thread")
def test_light_steel_thread_live_qualification_through_integration_tests(run_archive) -> None:
    workspace = run_archive.workspace
    install_real_sandbox(workspace, slug="steel_thread", archive=run_archive)
    seed_minimal_project_spec(workspace, archive=run_archive)
    assignments = _require_live_workers(workspace)
    run_archive.update_summary(selected_assignments=assignments)
    run_archive.note(
        "scenario",
        lane="live",
        through_edge=INTEGRATION_EDGE,
        assignments=assignments,
    )

    _emit_event(
        workspace,
        "intent_raised",
        {
            "feature": "STEEL-001",
            "summary": "simple intent to code and tests",
        },
        archive=run_archive,
        label="emit intent_raised",
    )

    max_steps = 20
    for _ in range(max_steps):
        gaps = _run_json(workspace, "gaps", archive=run_archive, label="genesis gaps")
        edge_map = {entry["edge"]: entry for entry in gaps["gaps"]}
        if edge_map[INTEGRATION_EDGE]["delta"] == 0:
            break

        iterate = _run_json(workspace, "iterate", archive=run_archive, label="genesis iterate")
        edge = iterate["edge"]
        blocking_reason = iterate.get("blocking_reason")

        if blocking_reason == "fh_gate":
            _emit_event(
                workspace,
                "approved",
                {
                    "kind": "fh_intent" if edge == "intent→requirements" else "fh_review",
                    "edge": edge,
                    "actor": "steel_thread_live_tester",
                },
                archive=run_archive,
                label=f"emit approved {edge}",
            )
            continue

        if blocking_reason == "fd_gap" and edge_artifact(edge) is not None:
            _repair_live_fd_gap(workspace, edge, archive=run_archive)
            continue

        if blocking_reason == "fp_dispatch":
            manifest = json.loads(Path(iterate["fp_manifest_path"]).read_text(encoding="utf-8"))
            _qualify_live_edge(workspace, manifest, archive=run_archive)
            continue

        raise AssertionError(f"unexpected iterate outcome: {iterate}")
    else:
        raise AssertionError(f"live steel thread did not reach {INTEGRATION_EDGE} within {max_steps} steps")

    final_gaps = _run_json(workspace, "gaps", archive=run_archive, label="genesis gaps final")
    run_archive.capture_json("gaps_final_live.json", final_gaps)
    final_edge_map = {entry["edge"]: entry for entry in final_gaps["gaps"]}
    run_archive.update_summary(
        lane="live",
        converged=final_gaps["converged"],
        total_delta=final_gaps["total_delta"],
        completed_edge=INTEGRATION_EDGE,
        target_edge_converged=final_edge_map[INTEGRATION_EDGE]["delta"] == 0,
    )

    assert final_edge_map["intent→requirements"]["delta"] == 0
    assert final_edge_map["requirements→feature_decomp"]["delta"] == 0
    assert final_edge_map["feature_decomp→design"]["delta"] == 0
    assert final_edge_map["design→module_decomp"]["delta"] == 0
    assert final_edge_map["module_decomp→code"]["delta"] == 0
    assert final_edge_map["module_decomp→unit_tests"]["delta"] == 0
    assert final_edge_map[INTEGRATION_EDGE]["delta"] == 0

    for edge in DOWNSTREAM_RELEASE_EDGES:
        assert final_edge_map[edge]["delta"] > 0


@pytest.mark.usecase_id("gsdlc_full_cycle")
def test_full_cycle_live_qualification_through_uat_acceptance(run_archive) -> None:
    workspace = run_archive.workspace
    install_real_sandbox(workspace, slug="full_cycle", archive=run_archive)
    seed_minimal_project_spec(workspace, archive=run_archive)
    assignments = _require_live_workers(workspace)
    run_archive.update_summary(selected_assignments=assignments)
    run_archive.note(
        "scenario",
        lane="live",
        through_edge=UAT_EDGE,
        assignments=assignments,
    )

    _emit_event(
        workspace,
        "intent_raised",
        {
            "feature": "FULL-001",
            "summary": "full cycle from intent to release acceptance",
        },
        archive=run_archive,
        label="emit intent_raised",
    )

    max_steps = 30
    for _ in range(max_steps):
        gaps = _run_json(workspace, "gaps", archive=run_archive, label="genesis gaps")
        edge_map = {entry["edge"]: entry for entry in gaps["gaps"]}
        if edge_map[UAT_EDGE]["delta"] == 0:
            break

        iterate = _run_json(workspace, "iterate", archive=run_archive, label="genesis iterate")
        edge = iterate["edge"]
        blocking_reason = iterate.get("blocking_reason")

        if blocking_reason == "fh_gate":
            _emit_event(
                workspace,
                "approved",
                {
                    "kind": "fh_intent" if edge == "intent→requirements" else "fh_review",
                    "edge": edge,
                    "actor": "full_cycle_live_tester",
                },
                archive=run_archive,
                label=f"emit approved {edge}",
            )
            continue

        if blocking_reason == "fd_gap" and edge_artifact(edge) is not None:
            _repair_live_fd_gap(workspace, edge, archive=run_archive)
            continue

        if blocking_reason == "fp_dispatch":
            manifest = json.loads(Path(iterate["fp_manifest_path"]).read_text(encoding="utf-8"))
            _qualify_live_edge(workspace, manifest, archive=run_archive)
            continue

        raise AssertionError(f"unexpected iterate outcome: {iterate}")
    else:
        raise AssertionError(f"live full cycle did not reach {UAT_EDGE} within {max_steps} steps")

    final_gaps = _run_json(workspace, "gaps", archive=run_archive, label="genesis gaps final")
    run_archive.capture_json("gaps_final_live.json", final_gaps)
    final_edge_map = {entry["edge"]: entry for entry in final_gaps["gaps"]}
    run_archive.update_summary(
        lane="live",
        converged=final_gaps["converged"],
        total_delta=final_gaps["total_delta"],
        completed_edge=UAT_EDGE,
        target_edge_converged=final_edge_map[UAT_EDGE]["delta"] == 0,
    )

    assert final_gaps["converged"] is True
    assert final_gaps["total_delta"] == 0
    assert final_edge_map["intent→requirements"]["delta"] == 0
    assert final_edge_map["requirements→feature_decomp"]["delta"] == 0
    assert final_edge_map["feature_decomp→design"]["delta"] == 0
    assert final_edge_map["design→module_decomp"]["delta"] == 0
    assert final_edge_map["module_decomp→code"]["delta"] == 0
    assert final_edge_map["module_decomp→unit_tests"]["delta"] == 0
    assert final_edge_map[INTEGRATION_EDGE]["delta"] == 0
    assert final_edge_map[USER_GUIDE_EDGE]["delta"] == 0
    assert final_edge_map[BOOTLOADER_EDGE]["delta"] == 0
    assert final_edge_map[UAT_EDGE]["delta"] == 0


@pytest.mark.usecase_id("gsdlc_role_split_live")
def test_live_role_split_routes_code_to_implementer_worker(run_archive) -> None:
    workspace = run_archive.workspace
    install_real_sandbox(workspace, slug="role_split_live", archive=run_archive)
    seed_minimal_project_spec(workspace, archive=run_archive)
    assignments = _require_live_workers(
        workspace,
        overrides={
            "constructor": "claude_code",
            "implementer": "codex",
        },
    )
    run_archive.update_summary(selected_assignments=assignments)
    run_archive.note(
        "scenario",
        lane="live",
        through_edge="module_decomp→code",
        assignments=assignments,
    )

    seen_assignments: dict[str, dict[str, str]] = {}
    _emit_event(
        workspace,
        "intent_raised",
        {
            "feature": "ROLE-SPLIT-001",
            "summary": "mixed worker assignment through code edge",
        },
        archive=run_archive,
        label="emit intent_raised role split",
    )

    max_steps = 15
    for _ in range(max_steps):
        gaps = _run_json(workspace, "gaps", archive=run_archive, label="genesis gaps")
        edge_map = {entry["edge"]: entry for entry in gaps["gaps"]}
        if edge_map["module_decomp→code"]["delta"] == 0:
            break

        iterate = _run_json(workspace, "iterate", archive=run_archive, label="genesis iterate")
        edge = iterate["edge"]
        blocking_reason = iterate.get("blocking_reason")

        if blocking_reason == "fh_gate":
            _emit_event(
                workspace,
                "approved",
                {
                    "kind": "fh_intent" if edge == "intent→requirements" else "fh_review",
                    "edge": edge,
                    "actor": "role_split_live_tester",
                },
                archive=run_archive,
                label=f"emit approved {edge}",
            )
            continue

        if blocking_reason == "fp_dispatch":
            manifest = json.loads(Path(iterate["fp_manifest_path"]).read_text(encoding="utf-8"))
            seen_assignments[edge] = _assignment_for_edge(workspace, edge)
            _qualify_live_edge(workspace, manifest, archive=run_archive)
            continue

        raise AssertionError(f"unexpected iterate outcome: {iterate}")
    else:
        raise AssertionError("live role split did not reach module_decomp→code within 15 steps")

    final_gaps = _run_json(workspace, "gaps", archive=run_archive, label="genesis gaps final")
    run_archive.capture_json("gaps_final_live.json", final_gaps)
    run_archive.capture_json("role_split_assignments.json", seen_assignments)

    assert seen_assignments["requirements→feature_decomp"]["role_id"] == "constructor"
    assert seen_assignments["requirements→feature_decomp"]["worker_id"] == "claude_code"
    assert seen_assignments["feature_decomp→design"]["role_id"] == "constructor"
    assert seen_assignments["feature_decomp→design"]["worker_id"] == "claude_code"
    assert seen_assignments["design→module_decomp"]["role_id"] == "constructor"
    assert seen_assignments["design→module_decomp"]["worker_id"] == "claude_code"
    assert seen_assignments["module_decomp→code"]["role_id"] == "implementer"
    assert seen_assignments["module_decomp→code"]["worker_id"] == "codex"


@pytest.mark.usecase_id("gsdlc_code_tests_split_live")
def test_focused_live_split_from_module_decomp_code_on_claude_tests_on_codex(run_archive) -> None:
    workspace = run_archive.workspace
    install_real_sandbox(workspace, slug="code_tests_split_live", archive=run_archive)
    seed_minimal_project_spec(workspace, archive=run_archive)
    assignments = _require_live_workers(
        workspace,
        overrides={
            "constructor": "codex",
            "implementer": "claude_code",
        },
    )
    run_archive.update_summary(selected_assignments=assignments)
    run_archive.note(
        "scenario",
        lane="focused_live",
        through_edges=["module_decomp→code", "module_decomp→unit_tests"],
        assignments=assignments,
    )

    _emit_event(
        workspace,
        "intent_raised",
        {
            "feature": "ROLE-SPLIT-002",
            "summary": "focused split from module decomposition to code and unit tests",
        },
        archive=run_archive,
        label="emit intent_raised focused split",
    )

    seen_assignments: dict[str, dict[str, str]] = {}

    max_steps = 20
    for _ in range(max_steps):
        gaps = _run_json(workspace, "gaps", archive=run_archive, label="genesis gaps")
        edge_map = {entry["edge"]: entry for entry in gaps["gaps"]}
        if (
            edge_map["design→module_decomp"]["delta"] == 0
            and edge_map["module_decomp→code"]["delta"] == 0
            and edge_map["module_decomp→unit_tests"]["delta"] == 0
        ):
            break

        iterate = _run_json(workspace, "iterate", archive=run_archive, label="genesis iterate")
        edge = iterate["edge"]
        blocking_reason = iterate.get("blocking_reason")

        if blocking_reason == "fh_gate":
            _emit_event(
                workspace,
                "approved",
                {
                    "kind": "fh_intent" if edge == "intent→requirements" else "fh_review",
                    "edge": edge,
                    "actor": "focused_split_live_tester",
                },
                archive=run_archive,
                label=f"emit approved {edge}",
            )
            continue

        if blocking_reason == "fp_dispatch":
            manifest = json.loads(Path(iterate["fp_manifest_path"]).read_text(encoding="utf-8"))
            seen_assignments[edge] = _assignment_for_edge(workspace, edge)
            if edge in {"module_decomp→code", "module_decomp→unit_tests"}:
                _qualify_live_edge(workspace, manifest, archive=run_archive)
            else:
                _qualify_fake_edge(workspace, manifest, archive=run_archive)
            continue

        raise AssertionError(f"unexpected iterate outcome: {iterate}")
    else:
        raise AssertionError("focused split live test did not converge through code and unit tests within 20 steps")

    final_gaps = _run_json(workspace, "gaps", archive=run_archive, label="genesis gaps final")
    run_archive.capture_json("gaps_final_live.json", final_gaps)
    run_archive.capture_json("focused_split_assignments.json", seen_assignments)

    final_edge_map = {entry["edge"]: entry for entry in final_gaps["gaps"]}
    assert final_edge_map["design→module_decomp"]["delta"] == 0
    assert final_edge_map["module_decomp→code"]["delta"] == 0
    assert final_edge_map["module_decomp→unit_tests"]["delta"] == 0
    assert seen_assignments["design→module_decomp"]["role_id"] == "constructor"
    assert seen_assignments["design→module_decomp"]["worker_id"] == "codex"
    assert seen_assignments["module_decomp→code"]["role_id"] == "implementer"
    assert seen_assignments["module_decomp→code"]["worker_id"] == "claude_code"
    assert seen_assignments["module_decomp→unit_tests"]["role_id"] == "constructor"
    assert seen_assignments["module_decomp→unit_tests"]["worker_id"] == "codex"
