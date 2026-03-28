# Validates: REQ-F-BOOT-001
# Validates: REQ-F-BOOT-002
# Validates: REQ-F-BOOT-003
# Validates: REQ-F-BOOT-004
# Validates: REQ-F-BOOT-007
# Validates: REQ-F-BOOT-008
# Validates: REQ-F-BOOT-009
# Validates: REQ-F-CUSTODY-002
# Validates: REQ-F-CMD-001
# Validates: REQ-F-GATE-001
# Validates: REQ-F-TEST-001
# Validates: REQ-F-UAT-001
# Validates: REQ-F-ASSURE-002
"""Sandbox tests for the installed Abiogenesis/Python genesis_sdlc workflow."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from .minimal_project import build_fake_artifact, edge_assessments, seed_minimal_project_spec, write_result_file
from .sandbox_runtime import install_real_sandbox, reset_runtime_sandbox, run_genesis


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
    assert active_workflow["customization"]["fp_transport_agent"] == "claude"
    assert ".claude/commands/" in active_workflow["managed_surfaces"]
    assert ".genesis/" in active_workflow["managed_surfaces"]
    assert ".gsdlc/release/" in active_workflow["managed_surfaces"]

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
