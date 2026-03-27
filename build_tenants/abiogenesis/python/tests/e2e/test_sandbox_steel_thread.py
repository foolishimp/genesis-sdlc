# Validates: REQ-F-CMD-001
# Validates: REQ-F-GATE-001
# Validates: REQ-F-GRAPH-001
# Validates: REQ-F-TEST-001
"""Light steel-thread test over the real genesis_sdlc workflow."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from .sandbox_runtime import install_real_sandbox, run_genesis


INTEGRATION_EDGE = "[code, unit_tests]→integration_tests"
DOWNSTREAM_RELEASE_EDGES = {
    "[design, integration_tests]→user_guide",
    "[requirements, design, integration_tests]→bootloader",
    "[requirements, integration_tests]→uat_tests",
}


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


def _write_passing_sandbox_report(workspace: Path) -> None:
    report_path = workspace / ".ai-workspace" / "uat" / "sandbox_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "all_pass": True,
                "scenario": "light_steel_thread",
                "notes": "integration edge evidence produced by sandbox steel-thread test",
            },
            indent=2,
        ),
        encoding="utf-8",
    )


@pytest.mark.e2e
@pytest.mark.usecase_id("gsdlc_steel_thread")
def test_light_steel_thread_converges_through_integration_tests(run_archive) -> None:
    workspace = run_archive.workspace
    install_real_sandbox(workspace, slug="steel_thread", archive=run_archive)
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

        if edge == INTEGRATION_EDGE:
            _write_passing_sandbox_report(workspace)

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
            for evaluator in manifest["failing_evaluators"]:
                _emit_event(
                    workspace,
                    "assessed",
                    {
                        "kind": "fp",
                        "edge": edge,
                        "evaluator": evaluator["name"],
                        "actor": "steel_thread_tester",
                        "result": "pass",
                        "evidence": f"{evaluator['name']} accepted in light steel thread",
                        "spec_hash": manifest["spec_hash"],
                    },
                    archive=run_archive,
                    label=f"emit assessed {edge} {evaluator['name']}",
                )
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
