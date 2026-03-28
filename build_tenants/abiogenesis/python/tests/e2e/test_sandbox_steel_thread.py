# Validates: REQ-F-CMD-001
# Validates: REQ-F-GATE-001
# Validates: REQ-F-GRAPH-001
# Validates: REQ-F-TEST-001
# Validates: REQ-F-MVP-002
# Validates: REQ-F-ASSURE-002
"""Light steel-thread test over the real genesis_sdlc workflow."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from .minimal_project import (
    DOWNSTREAM_RELEASE_EDGES,
    INTEGRATION_EDGE,
    build_fake_artifact,
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
@pytest.mark.usecase_id("gsdlc_steel_thread")
def test_light_steel_thread_converges_through_integration_tests(run_archive) -> None:
    workspace = run_archive.workspace
    install_real_sandbox(workspace, slug="steel_thread", archive=run_archive)
    seed_minimal_project_spec(workspace, archive=run_archive)
    run_archive.note("scenario", lane="steel_thread", through_edge=INTEGRATION_EDGE)

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
                    "actor": "steel_thread_tester",
                },
                archive=run_archive,
                label=f"emit approved {edge}",
            )
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
                actor="steel_thread_tester",
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
        raise AssertionError(f"steel thread did not reach {INTEGRATION_EDGE} within {max_steps} steps")

    final_gaps = _run_json(workspace, "gaps", archive=run_archive, label="genesis gaps final")
    run_archive.capture_json("gaps_final.json", final_gaps)
    final_edge_map = {entry["edge"]: entry for entry in final_gaps["gaps"]}
    run_archive.update_summary(
        converged=final_edge_map[INTEGRATION_EDGE]["delta"] == 0,
        total_delta=final_gaps["total_delta"],
        completed_edge=INTEGRATION_EDGE,
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
