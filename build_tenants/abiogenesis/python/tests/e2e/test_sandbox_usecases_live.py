# Validates: REQ-F-CMD-001
# Validates: REQ-F-TEST-001
# Validates: REQ-F-TEST-004
# Validates: REQ-F-TEST-005
"""Live qualification lane for sandbox-backed workflow scenarios."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

from genesis_sdlc.evidence.uat import write_sandbox_report

from .live_transport import call_agent, has_agent
from .minimal_project import (
    BOOTLOADER_ARTIFACT,
    BOOTLOADER_EDGE,
    BOOTLOADER_RELEASE_COPY,
    DOWNSTREAM_RELEASE_EDGES,
    INTEGRATION_EDGE,
    UAT_EDGE,
    USER_GUIDE_EDGE,
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


def _live_agent() -> str:
    return os.environ.get("GSDLC_LIVE_AGENT", "codex")


def _live_enabled() -> bool:
    return os.environ.get("CODEX_LIVE_FP") == "1" and has_agent(_live_agent())


def _word_count(text: str) -> int:
    return len(text.split())


def _safe_stem(edge: str) -> str:
    return edge.replace("→", "_").replace("[", "").replace("]", "").replace(", ", "_").replace(" ", "")


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


def _qualify_live_edge(workspace: Path, manifest: dict, *, archive, agent: str) -> None:
    edge = manifest["edge"]
    relative_artifact = edge_artifact(edge)
    if relative_artifact is None:
        raise KeyError(f"no live artifact target declared for edge: {edge}")

    prompt = constructive_prompt(edge, manifest, artifact_path=relative_artifact)
    artifact = workspace / relative_artifact
    artifact.parent.mkdir(parents=True, exist_ok=True)

    safe_stem = _safe_stem(edge)
    archive.capture_text(f"{safe_stem}_prompt.txt", prompt)
    archive.capture_json(f"{safe_stem}_manifest.json", manifest)
    archive.update_summary(prompt_words=_word_count(prompt), transport_agent=agent)

    response = call_agent(prompt, str(workspace), agent=agent, timeout=360)
    archive.capture_text(f"{safe_stem}_raw_response.txt", response)

    if edge == INTEGRATION_EDGE:
        write_sandbox_report(
            workspace / ".ai-workspace" / "uat" / "sandbox_report.json",
            scenario="live_qualification",
            sandbox_path=str(workspace),
        )

    if edge == BOOTLOADER_EDGE and artifact.exists():
        release_copy = workspace / BOOTLOADER_RELEASE_COPY
        release_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(artifact, release_copy)

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


def _repair_live_fd_gap(workspace: Path, edge: str, *, archive, agent: str) -> None:
    relative_artifact = edge_artifact(edge)
    if relative_artifact is None:
        raise KeyError(f"no repair artifact declared for edge: {edge}")

    prompt = fd_repair_prompt(edge, workspace)
    artifact = workspace / relative_artifact
    artifact.parent.mkdir(parents=True, exist_ok=True)

    safe_stem = _safe_stem(f"{edge}_repair")
    archive.capture_text(f"{safe_stem}_prompt.txt", prompt)
    response = call_agent(prompt, str(workspace), agent=agent, timeout=360)
    archive.capture_text(f"{safe_stem}_raw_response.txt", response)

    if edge == BOOTLOADER_EDGE and artifact.exists():
        release_copy = workspace / BOOTLOADER_RELEASE_COPY
        release_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(artifact, release_copy)

    archive.copy_file(artifact, dest_name=f"repair_{artifact.name}")


@pytest.mark.usecase_id("workflow_fp_dispatch")
@pytest.mark.skipif(
    not _live_enabled(),
    reason="set CODEX_LIVE_FP=1 and ensure the selected agent CLI is available",
)
def test_workflow_advances_from_fh_gate_to_live_fp_qualification(run_archive) -> None:
    workspace = run_archive.workspace
    agent = _live_agent()
    install_real_sandbox(workspace, archive=run_archive)
    seed_minimal_project_spec(workspace, archive=run_archive)
    run_archive.note("scenario", lane="live", edge="requirements→feature_decomp", agent=agent)

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
    run_archive.capture_json("fp_live_manifest.json", manifest)
    run_archive.update_summary(
        lane="live",
        edge=manifest["edge"],
        manifest_id=manifest["manifest_id"],
        result_path=manifest["result_path"],
        transport_agent=agent,
    )

    _qualify_live_edge(workspace, manifest, archive=run_archive, agent=agent)

    gaps = _run_json(workspace, "gaps", archive=run_archive, label="genesis gaps after live fp")
    run_archive.capture_json("gaps_after_live_fp.json", gaps)
    edge_map = {entry["edge"]: entry for entry in gaps["gaps"]}
    run_archive.update_summary(total_delta=gaps["total_delta"], converged=gaps["converged"])

    assert "feature_decomp_complete" not in edge_map["requirements→feature_decomp"]["failing"]


@pytest.mark.usecase_id("gsdlc_steel_thread")
@pytest.mark.skipif(
    not _live_enabled(),
    reason="set CODEX_LIVE_FP=1 and ensure the selected agent CLI is available",
)
def test_light_steel_thread_live_qualification_through_integration_tests(run_archive) -> None:
    workspace = run_archive.workspace
    agent = _live_agent()
    install_real_sandbox(workspace, slug="steel_thread", archive=run_archive)
    seed_minimal_project_spec(workspace, archive=run_archive)
    run_archive.note("scenario", lane="live", through_edge=INTEGRATION_EDGE, agent=agent)

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
            _repair_live_fd_gap(workspace, edge, archive=run_archive, agent=agent)
            continue

        if blocking_reason == "fp_dispatch":
            manifest = json.loads(Path(iterate["fp_manifest_path"]).read_text(encoding="utf-8"))
            _qualify_live_edge(workspace, manifest, archive=run_archive, agent=agent)
            continue

        raise AssertionError(f"unexpected iterate outcome: {iterate}")
    else:
        raise AssertionError(f"live steel thread did not reach {INTEGRATION_EDGE} within {max_steps} steps")

    final_gaps = _run_json(workspace, "gaps", archive=run_archive, label="genesis gaps final")
    run_archive.capture_json("gaps_final_live.json", final_gaps)
    final_edge_map = {entry["edge"]: entry for entry in final_gaps["gaps"]}
    run_archive.update_summary(
        lane="live",
        converged=final_edge_map[INTEGRATION_EDGE]["delta"] == 0,
        total_delta=final_gaps["total_delta"],
        completed_edge=INTEGRATION_EDGE,
        transport_agent=agent,
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
@pytest.mark.skipif(
    not _live_enabled(),
    reason="set CODEX_LIVE_FP=1 and ensure the selected agent CLI is available",
)
def test_full_cycle_live_qualification_through_uat_acceptance(run_archive) -> None:
    workspace = run_archive.workspace
    agent = _live_agent()
    install_real_sandbox(workspace, slug="full_cycle", archive=run_archive)
    seed_minimal_project_spec(workspace, archive=run_archive)
    run_archive.note("scenario", lane="live", through_edge=UAT_EDGE, agent=agent)

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
            _repair_live_fd_gap(workspace, edge, archive=run_archive, agent=agent)
            continue

        if blocking_reason == "fp_dispatch":
            manifest = json.loads(Path(iterate["fp_manifest_path"]).read_text(encoding="utf-8"))
            _qualify_live_edge(workspace, manifest, archive=run_archive, agent=agent)
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
        transport_agent=agent,
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
