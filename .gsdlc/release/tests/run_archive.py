# Validates: REQ-F-TEST-001
# Validates: REQ-F-TEST-004
# Validates: REQ-F-ASSURE-002
# Validates: REQ-F-ASSURE-003
"""Persistent run archive for sandbox-backed tenant tests."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_TESTS_DIR = Path(__file__).resolve().parent
_VARIANT_ROOT = _TESTS_DIR.parent
_RUNS_DIR = _VARIANT_ROOT / "test_runs"


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "unnamed"


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(_VARIANT_ROOT.parents[2]),
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return "unknown"
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip() or "unknown"


def _report_reason(report: Any | None) -> str | None:
    if report is None:
        return None
    longreprtext = getattr(report, "longreprtext", None)
    if isinstance(longreprtext, str) and longreprtext.strip():
        return longreprtext.strip().splitlines()[-1]
    longrepr = getattr(report, "longrepr", None)
    if longrepr is None:
        return None
    text = str(longrepr).strip()
    return text.splitlines()[-1] if text else None


@dataclass
class RunArchive:
    run_dir: Path
    workspace: Path
    artifacts_dir: Path
    usecase_id: str
    test_name: str
    timestamp: str
    notes: list[dict[str, Any]] = field(default_factory=list)
    summary_overrides: dict[str, Any] = field(default_factory=dict)
    _stdout_path: Path = field(init=False)
    _stderr_path: Path = field(init=False)
    _finalized: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self._stdout_path = self.run_dir / "stdout.log"
        self._stderr_path = self.run_dir / "stderr.log"
        self._stdout_path.touch()
        self._stderr_path.touch()

    def note(self, label: str, **data: Any) -> None:
        self.notes.append(
            {
                "label": label,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **data,
            }
        )

    def log_subprocess(self, label: str, result: subprocess.CompletedProcess[str]) -> None:
        args = result.args if isinstance(result.args, list) else [str(result.args)]
        self.note(
            "subprocess",
            subprocess_label=label,
            args=args,
            returncode=result.returncode,
        )
        with open(self._stdout_path, "a", encoding="utf-8") as handle:
            handle.write(f"--- {label} (exit {result.returncode}) ---\n")
            handle.write(result.stdout or "")
            handle.write("\n")
        with open(self._stderr_path, "a", encoding="utf-8") as handle:
            handle.write(f"--- {label} (exit {result.returncode}) ---\n")
            handle.write(result.stderr or "")
            handle.write("\n")

    def capture_text(self, name: str, text: str) -> Path:
        path = self.artifacts_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def capture_json(self, name: str, payload: Any) -> Path:
        path = self.artifacts_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def copy_file(self, source: Path, *, dest_name: str | None = None) -> Path | None:
        if not source.exists():
            return None
        destination = self.artifacts_dir / (dest_name or source.name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return destination

    def update_summary(self, **data: Any) -> None:
        self.summary_overrides.update(data)

    def finalize(self, *, test_passed: bool, outcome: str, outcome_stage: str | None = None, outcome_reason: str | None = None) -> None:
        if self._finalized:
            return
        self._finalized = True

        summary = self._build_summary()
        summary["test_passed"] = test_passed
        summary["test_outcome"] = outcome
        summary["outcome_stage"] = outcome_stage
        summary["outcome_reason"] = outcome_reason
        (self.run_dir / "summary.json").write_text(
            json.dumps(summary, indent=2),
            encoding="utf-8",
        )

        run_meta = {
            "usecase_id": self.usecase_id,
            "test_name": self.test_name,
            "timestamp": self.timestamp,
            "test_passed": test_passed,
            "test_outcome": outcome,
            "outcome_stage": outcome_stage,
            "outcome_reason": outcome_reason,
            "source_commit": _git_commit(),
            "python": sys.executable,
            "notes": self.notes,
        }
        (self.run_dir / "run.json").write_text(
            json.dumps(run_meta, indent=2),
            encoding="utf-8",
        )

        self._copy_workspace_artifacts()

    def _build_summary(self) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "usecase_id": self.usecase_id,
            "test_name": self.test_name,
            "workspace": str(self.workspace),
        }

        events_path = self.workspace / ".ai-workspace" / "events" / "events.jsonl"
        events: list[dict[str, Any]] = []
        if events_path.exists():
            for line in events_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    events.append(json.loads(line))
        summary["total_events"] = len(events)
        summary["event_types"] = sorted({event["event_type"] for event in events})
        summary["event_worker_ids"] = sorted(
            {
                str(data["worker_id"])
                for event in events
                if isinstance(event, dict)
                and isinstance((data := event.get("data")), dict)
                and isinstance(data.get("worker_id"), str)
                and data.get("worker_id")
            }
        )
        summary["event_build_ids"] = sorted(
            {
                str(data["build"])
                for event in events
                if isinstance(event, dict)
                and isinstance((data := event.get("data")), dict)
                and isinstance(data.get("build"), str)
                and data.get("build")
            }
        )
        summary["event_authority_refs"] = sorted(
            {
                str(data["authority_ref"])
                for event in events
                if isinstance(event, dict)
                and isinstance((data := event.get("data")), dict)
                and isinstance(data.get("authority_ref"), str)
                and data.get("authority_ref")
            }
        )

        manifests_dir = self.workspace / ".ai-workspace" / "fp_manifests"
        results_dir = self.workspace / ".ai-workspace" / "fp_results"
        summary["manifest_files"] = sorted(f.name for f in manifests_dir.glob("*.json")) if manifests_dir.exists() else []
        summary["result_files"] = sorted(f.name for f in results_dir.glob("*.json")) if results_dir.exists() else []

        summary.update(self.summary_overrides)
        selected_assignments = summary.get("selected_assignments")
        if not isinstance(selected_assignments, dict):
            role_assignments = summary.get("role_assignments")
            if isinstance(role_assignments, dict):
                selected_assignments = role_assignments
        selected_workers: set[str] = set()
        selected_backends: set[str] = set()
        if isinstance(selected_assignments, dict):
            for assignment in selected_assignments.values():
                if not isinstance(assignment, dict):
                    continue
                worker_id = assignment.get("worker_id")
                backend = assignment.get("backend")
                if isinstance(worker_id, str) and worker_id:
                    selected_workers.add(worker_id)
                if isinstance(backend, str) and backend:
                    selected_backends.add(backend)
        selected_worker = summary.get("selected_worker") or summary.get("transport_agent")
        selected_backend = summary.get("selected_backend")
        if isinstance(selected_worker, str) and selected_worker:
            selected_workers.add(selected_worker)
        if isinstance(selected_backend, str) and selected_backend:
            selected_backends.add(selected_backend)
        if selected_workers:
            summary["selected_workers"] = sorted(selected_workers)
            summary["assignment_worker_ids"] = sorted(selected_workers)
        if selected_backends:
            summary["selected_backends"] = sorted(selected_backends)
        if selected_workers:
            event_worker_ids = [wid for wid in summary.get("event_worker_ids", []) if isinstance(wid, str)]
            event_authority_refs = [ref for ref in summary.get("event_authority_refs", []) if isinstance(ref, str)]
            provenance_warnings: list[str] = []
            router_dispatch = "runtime://role-dispatch" in event_authority_refs
            if router_dispatch:
                summary["worker_provenance_mode"] = "router_dispatch"
                summary["engine_worker_ids"] = event_worker_ids
                summary["engine_build_ids"] = [
                    bid for bid in summary.get("event_build_ids", []) if isinstance(bid, str)
                ]
                if not event_worker_ids:
                    provenance_warnings.append(
                        "router-dispatch run emitted no event worker_id values; engine worker provenance is incomplete"
                    )
            else:
                summary["worker_provenance_mode"] = "direct_worker"
                if set(event_worker_ids) != selected_workers:
                    provenance_warnings.append(
                        "event worker_id values do not match the resolved assignment worker set"
                    )
            if provenance_warnings:
                summary["worker_provenance_consistent"] = False
                summary["provenance_warnings"] = provenance_warnings
            else:
                summary["worker_provenance_consistent"] = True
        if selected_backends:
            summary["backend_identity"] = sorted(selected_backends)
        return summary

    def _copy_workspace_artifacts(self) -> None:
        for relative, dest_name in (
            (Path(".ai-workspace/events/events.jsonl"), "events.jsonl"),
            (Path(".ai-workspace/runtime/resolved-runtime.json"), "resolved-runtime.json"),
            (Path(".ai-workspace/runtime/doctor.json"), "doctor.json"),
            (Path(".gsdlc/release/runtime/workers.json"), "workers.json"),
            (Path(".gsdlc/release/runtime/role-assignments.json"), "role-assignments.json"),
            (Path(".ai-workspace/uat/sandbox_report.json"), "sandbox_report.json"),
            (Path(".genesis/genesis.yml"), "genesis.runtime.yml"),
            (Path(".gsdlc/release/genesis.yml"), "gsdlc.runtime.yml"),
            (Path(".gsdlc/release/active-workflow.json"), "active-workflow.json"),
            (Path(".gsdlc/release/USER_GUIDE.md"), "USER_GUIDE.md"),
            (Path(".gsdlc/release/SDLC_BOOTLOADER.md"), "SDLC_BOOTLOADER.md"),
        ):
            self.copy_file(self.workspace / relative, dest_name=dest_name)

        manifests_dir = self.workspace / ".ai-workspace" / "fp_manifests"
        if manifests_dir.exists():
            for manifest in manifests_dir.glob("*.json"):
                self.copy_file(manifest, dest_name=f"manifest_{manifest.name}")

        results_dir = self.workspace / ".ai-workspace" / "fp_results"
        if results_dir.exists():
            for result in results_dir.glob("*.json"):
                self.copy_file(result, dest_name=f"result_{result.name}")


def create_run_archive(usecase_id: str, test_name: str) -> RunArchive:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    run_name = f"{timestamp}_{_safe_name(test_name)}"
    run_dir = _RUNS_DIR / _safe_name(usecase_id) / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    workspace = run_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    artifacts_dir = run_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    return RunArchive(
        run_dir=run_dir,
        workspace=workspace,
        artifacts_dir=artifacts_dir,
        usecase_id=_safe_name(usecase_id),
        test_name=test_name,
        timestamp=timestamp,
    )
