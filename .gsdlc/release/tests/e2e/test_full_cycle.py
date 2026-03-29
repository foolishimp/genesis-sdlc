# Validates: REQ-F-CMD-001
# Validates: REQ-F-GATE-001
# Validates: REQ-F-DOCS-002
# Validates: REQ-F-UAT-003
# Validates: REQ-F-BOOTDOC-001
# Validates: REQ-F-TEST-001
# Validates: REQ-F-TEST-005
# Validates: REQ-F-MVP-003
# Validates: REQ-F-ASSURE-003
"""Full-cycle sandbox qualification through release acceptance."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from .minimal_project import (
    BOOTLOADER_EDGE,
    INTEGRATION_EDGE,
    UAT_EDGE,
    USER_GUIDE_EDGE,
    build_fake_artifact,
    edge_artifact,
    edge_assessments,
    seed_minimal_project_spec,
    write_result_file,
)
from .sandbox_runtime import install_real_sandbox, run_genesis


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


@pytest.mark.e2e
@pytest.mark.usecase_id("gsdlc_full_cycle")
def test_full_cycle_converges_through_uat_acceptance(run_archive) -> None:
    workspace = run_archive.workspace
    install_real_sandbox(workspace, slug="full_cycle", archive=run_archive)
    seed_minimal_project_spec(workspace, archive=run_archive)
    run_archive.note("scenario", lane="fake", through_edge=UAT_EDGE)

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
                    "actor": "full_cycle_tester",
                },
                archive=run_archive,
                label=f"emit approved {edge}",
            )
            continue

        if blocking_reason == "fd_gap" and edge_artifact(edge) is not None:
            artifact = build_fake_artifact(edge, workspace)
            run_archive.copy_file(artifact, dest_name=artifact.name)
            continue

        if blocking_reason == "fp_dispatch":
            manifest = json.loads(Path(iterate["fp_manifest_path"]).read_text(encoding="utf-8"))
            run_archive.capture_json(f"manifest_{edge.replace('→', '_')}.json", manifest)
            artifact = build_fake_artifact(edge, workspace, manifest)
            run_archive.copy_file(artifact, dest_name=artifact.name)
            result_path = Path(manifest["result_path"])
            write_result_file(
                result_path,
                edge=edge,
                actor="full_cycle_tester",
                assessments=edge_assessments(edge, workspace, manifest),
            )
            run_archive.capture_json(
                f"result_{edge.replace('→', '_')}.json",
                json.loads(result_path.read_text(encoding="utf-8")),
            )
            assessed = run_genesis(
                workspace,
                "assess-result",
                "--result",
                str(result_path),
                archive=run_archive,
                label=f"genesis assess-result {edge}",
            )
            assert assessed.returncode == 0, assessed.stderr
            continue

        raise AssertionError(f"unexpected iterate outcome: {iterate}")
    else:
        raise AssertionError(f"full cycle did not reach {UAT_EDGE} within {max_steps} steps")

    final_gaps = _run_json(workspace, "gaps", archive=run_archive, label="genesis gaps final")
    run_archive.capture_json("gaps_final.json", final_gaps)
    final_edge_map = {entry["edge"]: entry for entry in final_gaps["gaps"]}
    run_archive.update_summary(
        converged=final_gaps["converged"],
        total_delta=final_gaps["total_delta"],
        completed_edge=UAT_EDGE,
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
