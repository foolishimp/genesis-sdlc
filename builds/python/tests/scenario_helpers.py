# Validates: REQ-F-TEST-001
# Validates: REQ-F-UAT-001
"""
Shared kernel infrastructure for gsdlc integration test scenarios.

Provides the plumbing that every integration test needs — install, env,
run, emit, read, assert — so each test file focuses on its own graph
walk scenarios and truth assertions.

RunArchive: persistent forensic archive for every test run.
  tests/runs/<usecase_id>/<sortable_datetime>/
    workspace/       — full sandbox snapshot (immutable after run)
    run.json         — provenance: commit, timestamp, commands, exit codes
    stdout.log       — accumulated subprocess stdout
    stderr.log       — accumulated subprocess stderr
    summary.json     — converged/failed, evaluators, artifact paths
    artifacts/       — copies of manifests, result files

Rules:
  - Each run directory is immutable once written
  - Never overwrite a prior run
  - Failed runs are at least as valuable as passing runs

Not a test file — pytest will not collect this module.
"""
import json
import os
import secrets
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Callable


_INSTALL_SCRIPT = (
    Path(__file__).resolve().parent.parent / "src" / "genesis_sdlc" / "install.py"
)
_RUNS_DIR = Path(__file__).resolve().parent.parent / "test_runs"


# ══════════════════════════════════════════════════════════════════════════════
# RunArchive — persistent forensic archive
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class RunArchive:
    """Persistent archive for a single test run."""
    run_dir: Path
    workspace: Path
    artifacts_dir: Path
    usecase_id: str
    test_name: str
    timestamp: str
    _commands: list = field(default_factory=list)
    _stdout_path: Path = field(init=False)
    _stderr_path: Path = field(init=False)
    _finalized: bool = field(default=False)

    def __post_init__(self):
        self._stdout_path = self.run_dir / "stdout.log"
        self._stderr_path = self.run_dir / "stderr.log"

    def log_subprocess(self, label: str, result: subprocess.CompletedProcess) -> None:
        self._commands.append({
            "label": label,
            "args": result.args if isinstance(result.args, list) else str(result.args),
            "returncode": result.returncode,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        with open(self._stdout_path, "a") as f:
            f.write(f"─── {label} (exit {result.returncode}) ───\n")
            f.write(result.stdout or "")
            f.write("\n")
        with open(self._stderr_path, "a") as f:
            f.write(f"─── {label} (exit {result.returncode}) ───\n")
            f.write(result.stderr or "")
            f.write("\n")

    def finalize(self, *, test_passed: bool = True) -> None:
        if self._finalized:
            return
        self._finalized = True

        summary = self._build_summary()
        (self.run_dir / "summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8")

        run_meta = {
            "usecase_id": self.usecase_id,
            "test_name": self.test_name,
            "timestamp": self.timestamp,
            "test_passed": test_passed,
            "source_commit": _get_git_commit(),
            "installer": str(_INSTALL_SCRIPT),
            "python": sys.executable,
            "commands": self._commands,
        }
        (self.run_dir / "run.json").write_text(
            json.dumps(run_meta, indent=2), encoding="utf-8")

        self._copy_artifacts()

    def _build_summary(self) -> dict:
        events = read_events(self.workspace)
        summary: dict = {
            "usecase_id": self.usecase_id,
            "test_name": self.test_name,
            "total_events": len(events),
            "event_types": list({e["event_type"] for e in events}),
        }
        try:
            gaps_data = run_genesis_json(
                self.workspace, "gaps", archive=self, label="finalize gaps")
            summary["converged"] = gaps_data.get("converged")
            summary["total_delta"] = gaps_data.get("total_delta")
            summary["failing_evaluators"] = [
                f for g in gaps_data.get("gaps", []) for f in g.get("failing", [])
            ]
        except (AssertionError, json.JSONDecodeError):
            summary["converged"] = None
            summary["total_delta"] = None
            summary["failing_evaluators"] = []
        return summary

    def _copy_artifacts(self) -> None:
        for subdir in ["fp_manifests", "fp_results"]:
            src = self.workspace / ".ai-workspace" / subdir
            if src.exists():
                for f in src.glob("*.json"):
                    shutil.copy2(f, self.artifacts_dir / f"{subdir}_{f.name}")
        efile = self.workspace / ".ai-workspace" / "events" / "events.jsonl"
        if efile.exists():
            shutil.copy2(efile, self.artifacts_dir / "events.jsonl")


_archive_counter = 0


def create_run_archive(usecase_id: str, test_name: str) -> RunArchive:
    global _archive_counter
    _archive_counter += 1
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    suffix = f"{_archive_counter:04d}_{secrets.token_hex(2)}"
    run_name = f"{ts}_{suffix}_{test_name}"
    run_dir = _RUNS_DIR / usecase_id / run_name
    run_dir.mkdir(parents=True, exist_ok=False)
    workspace = run_dir / "workspace"
    workspace.mkdir(exist_ok=True)
    artifacts = run_dir / "artifacts"
    artifacts.mkdir(exist_ok=True)
    return RunArchive(
        run_dir=run_dir, workspace=workspace, artifacts_dir=artifacts,
        usecase_id=usecase_id, test_name=test_name, timestamp=ts,
    )


def _get_git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


# ══════════════════════════════════════════════════════════════════════════════
# Sandbox install + environment
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_SLUG = "integration_test"


def install_sandbox(
    target: Path,
    project_slug: str = DEFAULT_SLUG,
    archive: Optional[RunArchive] = None,
) -> dict:
    """Run genesis_sdlc installer into a fresh target directory."""
    result = subprocess.run(
        [sys.executable, str(_INSTALL_SCRIPT),
         "--target", str(target),
         "--project-slug", project_slug],
        capture_output=True, text=True,
    )
    if archive:
        archive.log_subprocess("genesis_sdlc install", result)
    assert result.returncode == 0, (
        f"genesis_sdlc install failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    data = json.loads(result.stdout)
    assert data["status"] == "installed", f"Unexpected install status: {data}"
    return data


def installed_env(target: Path) -> dict:
    """Environment for subprocess genesis invocations against an installed workspace.

    PYTHONPATH order: .gsdlc/release (domain layer) > .genesis (kernel).
    The domain layer shadows the ABG gtl_spec stub with the real wrapper.
    """
    env = os.environ.copy()
    paths = [
        str(target / ".gsdlc" / "release"),
        str(target / ".genesis"),
    ]
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join(paths + ([existing] if existing else []))
    return env


# ══════════════════════════════════════════════════════════════════════════════
# Subprocess runners
# ══════════════════════════════════════════════════════════════════════════════

def run_genesis(
    target: Path, *args: str,
    archive: Optional[RunArchive] = None,
    label: str = "",
    timeout: int = 30,
) -> subprocess.CompletedProcess:
    """Run an installed genesis command as subprocess."""
    result = subprocess.run(
        [sys.executable, "-m", "genesis", *args, "--workspace", str(target)],
        capture_output=True, text=True,
        cwd=str(target),
        env=installed_env(target),
        timeout=timeout,
    )
    if archive:
        archive.log_subprocess(label or f"genesis {' '.join(args)}", result)
    return result


def run_genesis_json(
    target: Path, *args: str,
    archive: Optional[RunArchive] = None,
    label: str = "",
) -> dict:
    """Run genesis command and parse JSON stdout."""
    result = run_genesis(target, *args, archive=archive, label=label)
    assert result.returncode == 0, (
        f"genesis {' '.join(args)} failed (exit {result.returncode}):\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    return json.loads(result.stdout)


def emit_event(
    target: Path, event_type: str, data: dict,
    archive: Optional[RunArchive] = None,
) -> subprocess.CompletedProcess:
    """Emit an event through the installed CLI."""
    result = subprocess.run(
        [sys.executable, "-m", "genesis", "emit-event",
         "--type", event_type,
         "--data", json.dumps(data),
         "--workspace", str(target)],
        capture_output=True, text=True,
        cwd=str(target),
        env=installed_env(target),
    )
    if archive:
        archive.log_subprocess(f"emit-event {event_type}", result)
    return result


def read_events(target: Path) -> list[dict]:
    """Read all events from the installed workspace event log."""
    events_path = target / ".ai-workspace" / "events" / "events.jsonl"
    if not events_path.exists():
        return []
    events = []
    for line in events_path.read_text().strip().split("\n"):
        if line.strip():
            events.append(json.loads(line))
    return events


def compute_spec_hash(
    target: Path,
    project_slug: str = DEFAULT_SLUG,
    edge_name: str = "",
    archive: Optional[RunArchive] = None,
) -> str:
    """Compute the current spec_hash using the same logic as the engine.

    The engine reads active_workflow_path from the runtime contract (genesis.yml).
    When workflow_version != "unknown", it uses job_evaluator_hash(job) per edge.
    When "unknown", it falls back to req_hash(package.requirements).
    """
    result = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(f"""\
            import json, sys, yaml
            from pathlib import Path
            sys.path.insert(0, '.gsdlc/release')
            sys.path.insert(0, '.genesis')
            from genesis.bind import req_hash, job_evaluator_hash
            from genesis.commands import _read_workflow_version
            from gtl_spec.packages.{project_slug} import package, worker

            # Read active_workflow_path from runtime contract (same as CLI)
            active_workflow_path = None
            for cfg_path in [
                Path('.gsdlc/release/genesis.yml'),
                Path('.genesis/genesis.yml'),
            ]:
                if cfg_path.exists():
                    try:
                        cfg = yaml.safe_load(cfg_path.read_text())
                        if cfg and 'runtime_contract' in cfg:
                            rc = Path(cfg['runtime_contract'])
                            if rc.exists():
                                rc_data = yaml.safe_load(rc.read_text())
                                active_workflow_path = rc_data.get('active_workflow')
                                break
                        if cfg:
                            active_workflow_path = cfg.get('active_workflow')
                            if active_workflow_path:
                                break
                    except Exception:
                        pass

            wv = _read_workflow_version(Path('.'), active_workflow_path)

            edge_name = {edge_name!r}
            if wv == 'unknown':
                print(req_hash(package.requirements))
            else:
                job = None
                if edge_name:
                    for j in worker.can_execute:
                        if j.edge.name == edge_name:
                            job = j
                            break
                if job is None:
                    job = worker.can_execute[0]
                print(job_evaluator_hash(job))
        """)],
        capture_output=True, text=True,
        cwd=str(target),
        env=installed_env(target),
    )
    if archive:
        archive.log_subprocess(f"compute_spec_hash({edge_name or 'default'})", result)
    assert result.returncode == 0, f"Failed to compute spec_hash:\n{result.stderr}"
    return result.stdout.strip()


# ══════════════════════════════════════════════════════════════════════════════
# Per-hop artifact writers
#
# Each function creates the workspace artifacts needed for a specific edge's
# F_D evaluators to pass. These simulate what the F_P actor would produce.
# ══════════════════════════════════════════════════════════════════════════════

# ── Edge names (from instantiate()) ──────────────────────────────────────────
EDGE_INTENT_REQ       = "intent→requirements"
EDGE_REQ_FEAT         = "requirements→feature_decomp"
EDGE_FEAT_DESIGN      = "feature_decomp→design"
EDGE_DESIGN_MDECOMP   = "design→module_decomp"
EDGE_MDECOMP_CODE     = "module_decomp→code"
EDGE_TDD              = "code↔unit_tests"
EDGE_UNIT_ITEST       = "unit_tests→integration_tests"
EDGE_ITEST_GUIDE      = "integration_tests→user_guide"
EDGE_GUIDE_UAT        = "user_guide→uat_tests"

ALL_EDGES = [
    EDGE_INTENT_REQ, EDGE_REQ_FEAT, EDGE_FEAT_DESIGN, EDGE_DESIGN_MDECOMP,
    EDGE_MDECOMP_CODE, EDGE_TDD, EDGE_UNIT_ITEST, EDGE_ITEST_GUIDE, EDGE_GUIDE_UAT,
]

# ── Evaluator names (from sdlc_graph.py) ────────────────────────────────────
# F_H evaluators
EVAL_INTENT_FH        = "intent_approved"
EVAL_DECOMP_FH        = "decomp_approved"
EVAL_DESIGN_FH        = "design_approved"
EVAL_SCHEDULE_FH      = "schedule_approved"
EVAL_UAT_FH           = "uat_accepted"

# F_P evaluators
EVAL_DECOMP_FP        = "decomp_complete"
EVAL_DESIGN_FP        = "design_coherent"
EVAL_CODE_FP          = "code_complete"
EVAL_COVERAGE_FP      = "coverage_complete"
EVAL_SANDBOX_FP       = "sandbox_e2e_passed"
EVAL_GUIDE_FP         = "guide_content_certified"
EVAL_MODULE_FP        = "module_schedule"

# F_D evaluators
EVAL_REQ_COVERAGE     = "req_coverage"
EVAL_FEATURE_DAG      = "feature_dag_acyclic"
EVAL_BUILD_SCHEDULE   = "build_schedule_valid"
EVAL_MODULE_COVERAGE  = "module_coverage"
EVAL_IMPL_TAGS        = "impl_tags"
EVAL_TESTS_PASS       = "tests_pass"
EVAL_TEST_TAGS        = "validates_tags"
EVAL_E2E_EXISTS       = "e2e_tests_exist"
EVAL_SANDBOX_REPORT   = "sandbox_report_exists"
EVAL_GUIDE_VERSION    = "guide_version_current"
EVAL_GUIDE_COVERAGE   = "guide_req_coverage"


def write_intent(target: Path) -> None:
    """Write specification/INTENT.md."""
    spec_dir = target / "specification"
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "INTENT.md").write_text(textwrap.dedent("""\
        # INT-001 — Integration Test Project

        ## Problem Statement
        A test project for verifying the gsdlc graph walk.

        ## Value Proposition
        Proves the 9-edge SDLC graph converges correctly.

        ## Scope
        Minimal: one REQ key, one feature, one module.

        ## Priority Strategy
        dependency_first
    """))


def write_requirements(target: Path, keys: list[str]) -> None:
    """Write specification/requirements.md with given REQ keys."""
    spec_dir = target / "specification"
    spec_dir.mkdir(parents=True, exist_ok=True)
    lines = ["# Requirements\n"]
    for key in keys:
        lines.append(f"### {key} — Test requirement\n")
        lines.append(f"Requirement {key} for integration testing.\n\n")
    (spec_dir / "requirements.md").write_text("\n".join(lines))


def write_features(
    target: Path, req_keys: list[str],
    feature_id: str = "FD-001",
    feature_name: str = "core_feature",
) -> None:
    """Write feature vector YAML + build_schedule.json covering all REQ keys."""
    features_dir = target / ".ai-workspace" / "features" / "active"
    features_dir.mkdir(parents=True, exist_ok=True)

    satisfies = "\n".join(f"  - {k}" for k in req_keys)
    (features_dir / f"{feature_id}.yml").write_text(textwrap.dedent(f"""\
        id: {feature_id}
        name: {feature_name}
        satisfies:
        {satisfies}
        depends_on: []
    """))

    schedule = {
        "priority_strategy": "dependency_first",
        "mvp_boundary": [feature_id],
        "schedule": [
            {
                "id": feature_id,
                "depends_on": [],
                "priority_score": 1,
                "rationale": "Single feature, no dependencies.",
            }
        ],
    }
    (target / ".ai-workspace" / "features" / "build_schedule.json").write_text(
        json.dumps(schedule, indent=2))


def write_adrs(target: Path, platform: str = "python") -> None:
    """Write a minimal ADR to builds/{platform}/design/adrs/."""
    adr_dir = target / "builds" / platform / "design" / "adrs"
    adr_dir.mkdir(parents=True, exist_ok=True)
    (adr_dir / "ADR-001-initial-design.md").write_text(textwrap.dedent("""\
        # ADR-001: Initial Design

        **Status**: Accepted

        ## Context
        Integration test project needs a minimal design.

        ## Decision
        Use a single module with a single source file.

        ## Consequences
        Simple, testable, minimal.
    """))


def write_modules(
    target: Path,
    feature_ids: list[str],
    module_id: str = "MOD-001",
    module_name: str = "core_module",
) -> None:
    """Write module YAML to .ai-workspace/modules/."""
    modules_dir = target / ".ai-workspace" / "modules"
    modules_dir.mkdir(parents=True, exist_ok=True)

    features_ref = "\n".join(f"  - {fid}" for fid in feature_ids)
    (modules_dir / f"{module_id}.yml").write_text(textwrap.dedent(f"""\
        id: {module_id}
        name: {module_name}
        description: Core module for integration testing.
        implements_features:
        {features_ref}
        dependencies: []
        rank: 1
        interfaces:
          - name: main
            type: function
        source_files:
          - src/integration_test/core.py
    """))


def write_source_code(
    target: Path,
    slug: str = DEFAULT_SLUG,
    req_keys: list[str] | None = None,
) -> None:
    """Write source code with # Implements: tags."""
    req_keys = req_keys or ["REQ-F-IT-001"]
    src_dir = target / "builds" / "python" / "src" / slug
    src_dir.mkdir(parents=True, exist_ok=True)

    tags = "\n".join(f"# Implements: {k}" for k in req_keys)
    (src_dir / "__init__.py").write_text(f"{tags}\n")
    (src_dir / "core.py").write_text(
        f'{tags}\ndef main():\n    """Core function for integration testing."""\n    return "ok"\n'
    )


def write_tests(
    target: Path,
    slug: str = DEFAULT_SLUG,
    req_keys: list[str] | None = None,
) -> None:
    """Write test files with # Validates: tags."""
    req_keys = req_keys or ["REQ-F-IT-001"]
    test_dir = target / "builds" / "python" / "tests"
    test_dir.mkdir(parents=True, exist_ok=True)

    tags = "\n".join(f"# Validates: {k}" for k in req_keys)
    (test_dir / f"test_{slug}.py").write_text(
        f"{tags}\ndef test_core():\n    assert True\n\ndef test_main():\n    assert True\n"
    )


def write_e2e_test(target: Path, slug: str = DEFAULT_SLUG) -> None:
    """Write a minimal @pytest.mark.e2e test file."""
    test_dir = target / "builds" / "python" / "tests"
    test_dir.mkdir(parents=True, exist_ok=True)
    (test_dir / "test_e2e_minimal.py").write_text(textwrap.dedent(f"""\
        # Validates: REQ-F-IT-001
        import pytest

        @pytest.mark.e2e
        def test_e2e_smoke():
            \"\"\"Minimal e2e test for integration scenario.\"\"\"
            assert True
    """))


def write_sandbox_report(target: Path, all_pass: bool = True) -> None:
    """Write .ai-workspace/uat/sandbox_report.json."""
    uat_dir = target / ".ai-workspace" / "uat"
    uat_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "install_success": True,
        "sandbox_path": "/tmp/integration_test_sandbox",
        "test_count": 5,
        "pass_count": 5 if all_pass else 3,
        "fail_count": 0 if all_pass else 2,
        "all_pass": all_pass,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    (uat_dir / "sandbox_report.json").write_text(json.dumps(report, indent=2))


def write_user_guide(
    target: Path,
    version: str = "1.0.0b1",
    req_keys: list[str] | None = None,
) -> None:
    """Write docs/USER_GUIDE.md with version and <!-- Covers: --> tags."""
    req_keys = req_keys or ["REQ-F-IT-001"]
    docs_dir = target / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    covers = " ".join(req_keys)
    (docs_dir / "USER_GUIDE.md").write_text(textwrap.dedent(f"""\
        # User Guide

        **Version**: {version}

        ## Overview

        This guide covers the integration test project.

        <!-- Covers: {covers} -->

        ## Getting Started

        Run the project with `python -m {DEFAULT_SLUG}`.

        ## Features

        All features documented for integration testing.
    """))


def get_active_workflow_version(target: Path) -> str:
    """Read the active workflow version from the installed sandbox."""
    aw = target / ".gsdlc" / "release" / "active-workflow.json"
    if not aw.exists():
        return "unknown"
    data = json.loads(aw.read_text())
    return f"{data['workflow']}@{data['version']}"


# ══════════════════════════════════════════════════════════════════════════════
# Lifecycle helpers
# ══════════════════════════════════════════════════════════════════════════════

def approve_edge(
    target: Path, edge_name: str,
    actor: str = "test_human",
    archive: Optional[RunArchive] = None,
) -> None:
    """Emit an approved{kind: fh_review} event for an edge."""
    result = emit_event(target, "approved", {
        "kind": "fh_review",
        "edge": edge_name,
        "actor": actor,
    }, archive=archive)
    assert result.returncode == 0, (
        f"emit approved for {edge_name} failed:\n{result.stderr}"
    )


def assess_edge(
    target: Path, edge_name: str, evaluator: str,
    spec_hash: Optional[str] = None,
    project_slug: str = DEFAULT_SLUG,
    archive: Optional[RunArchive] = None,
) -> None:
    """Emit an assessed{kind: fp} event directly — TEST SHORTCUT.

    Bypasses the iterate → result_path → assess-result protocol.
    Prefer converge_edge_via_protocol() for F_P evaluators.
    Retained for edge cases where iterate cannot dispatch (e.g., F_D preconditions
    not met, or converging non-F_P evaluators).
    """
    if spec_hash is None:
        spec_hash = compute_spec_hash(target, project_slug, edge_name=edge_name, archive=archive)
    result = emit_event(target, "assessed", {
        "kind": "fp",
        "edge": edge_name,
        "evaluator": evaluator,
        "result": "pass",
        "spec_hash": spec_hash,
    }, archive=archive)
    assert result.returncode == 0, (
        f"emit assessed for {edge_name}/{evaluator} failed:\n{result.stderr}"
    )


def converge_edge_via_protocol(
    target: Path, edge_name: str, evaluator: str,
    project_slug: str = DEFAULT_SLUG,
    archive: Optional[RunArchive] = None,
) -> None:
    """Converge an F_P evaluator via iterate → result_path → assess-result.

    This is the correct protocol: iterate dispatches F_P and writes a manifest,
    we write a passing result to the result_path, then assess-result ingests it.
    Falls back to assess_edge if iterate cannot dispatch (already converged, error).
    """
    iter_result = run_genesis(target, "iterate", archive=archive, label=f"protocol-assess {edge_name}")
    if iter_result.returncode != 0:
        assess_edge(target, edge_name, evaluator, project_slug=project_slug, archive=archive)
        return
    data = json.loads(iter_result.stdout)
    if "fp_manifest_path" not in data:
        assess_edge(target, edge_name, evaluator, project_slug=project_slug, archive=archive)
        return
    manifest_path = Path(data["fp_manifest_path"])
    manifest_id = manifest_path.stem

    assessments = [{"evaluator": evaluator, "result": "pass",
                    "evidence": "test convergence via protocol"}]
    result_file = write_fp_result(target, manifest_id, edge_name, assessments,
                                  actor="test_protocol")
    r = assess_result(target, result_file, archive=archive)
    assert r.returncode == 0, f"assess-result failed for {edge_name}:\n{r.stderr}"


def write_fp_result(
    target: Path, manifest_id: str, edge_name: str,
    assessments: list[dict],
    actor: str = "test_agent",
) -> Path:
    """Write an F_P result JSON file to the result_path location."""
    results_dir = target / ".ai-workspace" / "fp_results"
    results_dir.mkdir(parents=True, exist_ok=True)
    result_file = results_dir / f"{manifest_id}.json"
    result_data = {
        "edge": edge_name,
        "actor": actor,
        "assessments": assessments,
    }
    result_file.write_text(json.dumps(result_data, indent=2), encoding="utf-8")
    return result_file


def assess_result(
    target: Path, result_path: Path,
    archive: Optional[RunArchive] = None,
) -> subprocess.CompletedProcess:
    """Ingest F_P result via the assess-result command."""
    result = subprocess.run(
        [sys.executable, "-m", "genesis", "assess-result",
         "--result", str(result_path),
         "--workspace", str(target)],
        capture_output=True, text=True,
        cwd=str(target),
        env=installed_env(target),
    )
    if archive:
        archive.log_subprocess("assess-result", result)
    return result


def dispatch_fp_and_read_manifest(
    target: Path,
    archive: Optional[RunArchive] = None,
) -> Optional[dict]:
    """Run iterate, return the manifest JSON if F_P was dispatched (exit 0)."""
    result = run_genesis(target, "iterate", archive=archive)
    if result.returncode != 0:
        return None
    data = json.loads(result.stdout)
    if "fp_manifest_path" not in data:
        return None
    manifest_path = Path(data["fp_manifest_path"])
    if not manifest_path.exists():
        return None
    return json.loads(manifest_path.read_text())


# ── Converge individual edges ────────────────────────────────────────────────

def converge_intent_to_requirements(
    target: Path,
    archive: Optional[RunArchive] = None,
) -> None:
    """Converge edge 1: intent→requirements (F_H only)."""
    approve_edge(target, EDGE_INTENT_REQ, archive=archive)


def converge_requirements_to_feature_decomp(
    target: Path,
    req_keys: list[str],
    archive: Optional[RunArchive] = None,
) -> None:
    """Converge edge 2: requirements→feature_decomp (F_D + F_P + F_H)."""
    write_features(target, req_keys)
    converge_edge_via_protocol(target, EDGE_REQ_FEAT, EVAL_DECOMP_FP, archive=archive)
    approve_edge(target, EDGE_REQ_FEAT, archive=archive)


def converge_feature_decomp_to_design(
    target: Path,
    archive: Optional[RunArchive] = None,
) -> None:
    """Converge edge 3: feature_decomp→design (F_P + F_H)."""
    write_adrs(target)
    converge_edge_via_protocol(target, EDGE_FEAT_DESIGN, EVAL_DESIGN_FP, archive=archive)
    approve_edge(target, EDGE_FEAT_DESIGN, archive=archive)


def converge_design_to_module_decomp(
    target: Path,
    feature_ids: list[str],
    archive: Optional[RunArchive] = None,
) -> None:
    """Converge edge 4: design→module_decomp (F_D + F_P + F_H)."""
    write_modules(target, feature_ids)
    converge_edge_via_protocol(target, EDGE_DESIGN_MDECOMP, EVAL_MODULE_FP, archive=archive)
    approve_edge(target, EDGE_DESIGN_MDECOMP, archive=archive)


def converge_module_decomp_to_code(
    target: Path,
    slug: str = DEFAULT_SLUG,
    req_keys: list[str] | None = None,
    archive: Optional[RunArchive] = None,
) -> None:
    """Converge edge 5: module_decomp→code (F_D + F_P)."""
    write_source_code(target, slug, req_keys)
    converge_edge_via_protocol(target, EDGE_MDECOMP_CODE, EVAL_CODE_FP, archive=archive)


def converge_tdd(
    target: Path,
    slug: str = DEFAULT_SLUG,
    req_keys: list[str] | None = None,
    archive: Optional[RunArchive] = None,
) -> None:
    """Converge edge 6: code↔unit_tests (F_D×3 + F_P)."""
    write_tests(target, slug, req_keys)
    write_e2e_test(target, slug)
    converge_edge_via_protocol(target, EDGE_TDD, EVAL_COVERAGE_FP, archive=archive)


def converge_unit_tests_to_integration_tests(
    target: Path,
    archive: Optional[RunArchive] = None,
) -> None:
    """Converge edge 7: unit_tests→integration_tests (F_D + F_P)."""
    write_sandbox_report(target)
    converge_edge_via_protocol(target, EDGE_UNIT_ITEST, EVAL_SANDBOX_FP, archive=archive)


def converge_integration_tests_to_user_guide(
    target: Path,
    req_keys: list[str] | None = None,
    archive: Optional[RunArchive] = None,
) -> None:
    """Converge edge 8: integration_tests→user_guide (F_D×2 + F_P + F_H)."""
    aw = target / ".gsdlc" / "release" / "active-workflow.json"
    version = "1.0.0b1"
    if aw.exists():
        version = json.loads(aw.read_text()).get("version", version)
    write_user_guide(target, version=version, req_keys=req_keys)
    converge_edge_via_protocol(target, EDGE_ITEST_GUIDE, EVAL_GUIDE_FP, archive=archive)
    approve_edge(target, EDGE_ITEST_GUIDE, archive=archive)


def converge_user_guide_to_uat(
    target: Path,
    archive: Optional[RunArchive] = None,
) -> None:
    """Converge edge 9: user_guide→uat_tests (F_H only)."""
    approve_edge(target, EDGE_GUIDE_UAT, archive=archive)


def converge_through_design(
    target: Path,
    req_keys: list[str] | None = None,
    archive: Optional[RunArchive] = None,
) -> None:
    """Converge edges 1-3: intent → requirements → feature_decomp → design."""
    req_keys = req_keys or ["REQ-F-IT-001"]
    write_intent(target)
    write_requirements(target, req_keys)
    converge_intent_to_requirements(target, archive=archive)
    converge_requirements_to_feature_decomp(target, req_keys, archive=archive)
    converge_feature_decomp_to_design(target, archive=archive)


def converge_through_code(
    target: Path,
    slug: str = DEFAULT_SLUG,
    req_keys: list[str] | None = None,
    archive: Optional[RunArchive] = None,
) -> None:
    """Converge edges 1-5: intent through code."""
    req_keys = req_keys or ["REQ-F-IT-001"]
    converge_through_design(target, req_keys, archive=archive)
    converge_design_to_module_decomp(target, ["FD-001"], archive=archive)
    converge_module_decomp_to_code(target, slug, req_keys, archive=archive)


def converge_through_unit_tests(
    target: Path,
    slug: str = DEFAULT_SLUG,
    req_keys: list[str] | None = None,
    archive: Optional[RunArchive] = None,
) -> None:
    """Converge edges 1-6: intent through unit_tests."""
    req_keys = req_keys or ["REQ-F-IT-001"]
    converge_through_code(target, slug, req_keys, archive=archive)
    converge_tdd(target, slug, req_keys, archive=archive)


def converge_full_graph(
    target: Path,
    slug: str = DEFAULT_SLUG,
    req_keys: list[str] | None = None,
    archive: Optional[RunArchive] = None,
) -> None:
    """Converge all 9 edges to delta=0."""
    req_keys = req_keys or ["REQ-F-IT-001"]
    converge_through_unit_tests(target, slug, req_keys, archive=archive)
    converge_unit_tests_to_integration_tests(target, archive=archive)
    converge_integration_tests_to_user_guide(target, req_keys, archive=archive)
    converge_user_guide_to_uat(target, archive=archive)


# ══════════════════════════════════════════════════════════════════════════════
# Assertion helpers
# ══════════════════════════════════════════════════════════════════════════════

def get_gaps(
    target: Path,
    archive: Optional[RunArchive] = None,
) -> dict:
    """Run gen-gaps and return parsed JSON."""
    return run_genesis_json(target, "gaps", archive=archive)


def get_edge_gap(
    target: Path, edge_name: str,
    archive: Optional[RunArchive] = None,
) -> Optional[dict]:
    """Get the gap entry for a specific edge, or None if not found."""
    data = get_gaps(target, archive=archive)
    for gap in data.get("gaps", []):
        if gap["edge"] == edge_name:
            return gap
    return None


def assert_edge_converged(
    target: Path, edge_name: str,
    archive: Optional[RunArchive] = None,
) -> None:
    """Assert that a specific edge has converged (delta=0)."""
    gap = get_edge_gap(target, edge_name, archive=archive)
    if gap is None:
        return  # Edge not in gaps → already converged and removed
    assert gap["delta"] == 0, (
        f"Expected {edge_name} delta=0, got delta={gap['delta']}, "
        f"failing={gap.get('failing', [])}"
    )


def assert_edge_in_delta(
    target: Path, edge_name: str,
    archive: Optional[RunArchive] = None,
) -> None:
    """Assert that a specific edge has delta > 0."""
    gap = get_edge_gap(target, edge_name, archive=archive)
    assert gap is not None, f"Edge {edge_name} not found in gaps"
    assert gap["delta"] > 0, (
        f"Expected {edge_name} delta>0, got delta={gap['delta']}"
    )


def assert_evaluator_failing(
    target: Path, edge_name: str, evaluator_name: str,
    archive: Optional[RunArchive] = None,
) -> None:
    """Assert that a specific evaluator is in the failing list for an edge."""
    gap = get_edge_gap(target, edge_name, archive=archive)
    assert gap is not None, f"Edge {edge_name} not found in gaps"
    assert evaluator_name in gap.get("failing", []), (
        f"Expected {evaluator_name} to be failing on {edge_name}, "
        f"failing={gap.get('failing', [])}, passing={gap.get('passing', [])}"
    )


def assert_evaluator_passing(
    target: Path, edge_name: str, evaluator_name: str,
    archive: Optional[RunArchive] = None,
) -> None:
    """Assert that a specific evaluator is in the passing list for an edge."""
    gap = get_edge_gap(target, edge_name, archive=archive)
    assert gap is not None, f"Edge {edge_name} not found in gaps"
    assert evaluator_name in gap.get("passing", []), (
        f"Expected {evaluator_name} to be passing on {edge_name}, "
        f"failing={gap.get('failing', [])}, passing={gap.get('passing', [])}"
    )


def assert_graph_converged(
    target: Path,
    archive: Optional[RunArchive] = None,
) -> None:
    """Assert that the full graph has converged (total_delta=0)."""
    data = get_gaps(target, archive=archive)
    assert data["converged"] is True, (
        f"Expected full convergence, got converged={data['converged']}, "
        f"total_delta={data['total_delta']}"
    )
    assert data["total_delta"] == 0


def assert_failure_inspectable(
    target: Path,
    archive: Optional[RunArchive] = None,
) -> None:
    """Assert that gap failures produce inspectable diagnostic evidence."""
    data = get_gaps(target, archive=archive)
    assert data["converged"] is False
    assert data["total_delta"] > 0
    for gap in data["gaps"]:
        assert "edge" in gap
        assert "delta" in gap
        assert "failing" in gap
        if gap["delta"] > 0:
            assert len(gap["failing"]) > 0


def assert_event_exists(
    target: Path, event_type: str,
    data_match: Optional[dict] = None,
) -> dict:
    """Assert an event of given type exists, optionally matching data fields."""
    events = read_events(target)
    matching = [e for e in events if e["event_type"] == event_type]
    assert matching, f"No {event_type} event found in stream"
    if data_match:
        for key, val in data_match.items():
            found = [e for e in matching if e.get("data", {}).get(key) == val]
            assert found, (
                f"No {event_type} event with data.{key}={val!r}, "
                f"found: {[e.get('data', {}).get(key) for e in matching]}"
            )
            matching = found
    return matching[-1]


def assert_event_chain(
    target: Path,
    *,
    edge_name: str,
    expect_converged: bool = True,
) -> None:
    """Assert the event audit trail is inspectable and explains the lifecycle."""
    events = read_events(target)
    types = [e["event_type"] for e in events]

    for e in events:
        assert "event_time" in e, f"Event missing event_time: {e['event_type']}"
        assert "event_type" in e

    if expect_converged:
        conv = [e for e in events if e["event_type"] == "edge_converged"
                and e.get("data", {}).get("edge") == edge_name]
        assert len(conv) >= 1, (
            f"edge_converged certificate for {edge_name} must be emitted"
        )
        cert = conv[-1]
        assert cert["data"]["delta"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# Live F_P qualification (real LLM invocation)
# ══════════════════════════════════════════════════════════════════════════════

JudgeFn = Callable[[Path, dict], list[dict]]


@dataclass
class LiveFpResult:
    """Result of a single live F_P invocation."""
    manifest: dict
    raw_response: str
    artifact_content: str
    model: str
    judge_assessments: list[dict]
    judge_passed: bool
    gaps_after: dict
    converged: bool
    failure_class: Optional[str] = None  # None=success, or transport_failure/no_output/wrong_output/quality_failure


# Wall-clock timeout for a single agent invocation (seconds).
# Mirrors ABG fp_dispatch.AGENT_CALL_TIMEOUT.
_AGENT_CALL_TIMEOUT = 300


class AgentTransportError(Exception):
    """Agent transport failure — process crash, timeout, not installed.

    Distinct from agent quality failures. Transport errors are retryable;
    quality failures need different prompts or escalation.
    """

    def __init__(self, message: str, failure_class: str = "transport_failure"):
        super().__init__(message)
        self.failure_class = failure_class


# Legacy alias
McpTransportError = AgentTransportError


def _has_mcp_transport() -> bool:
    """Check if the Claude Code CLI is available for F_P dispatch."""
    return shutil.which("claude") is not None


def _call_claude_code_mcp(
    prompt: str,
    work_folder: str,
    *,
    timeout: int = _AGENT_CALL_TIMEOUT,
) -> str:
    """Invoke Claude Code in a workspace via subprocess with env sanitization.

    Architecture: F_D → subprocess → agent
    Transport: `claude -p` with CLAUDE* env vars stripped to prevent nesting hang.

    When invoked from within an active Claude Code session, `claude -p` detects
    nesting guard env vars (CLAUDECODE, CLAUDE_CODE_SSE_PORT) and hangs.
    Stripping all CLAUDE* vars from the subprocess env fixes this.

    Inlined from ABG genesis.fp_dispatch.call_agent.

    Raises:
        AgentTransportError: if the agent times out, crashes, or is not installed.
    """
    if not shutil.which("claude"):
        raise AgentTransportError(
            "Claude Code CLI not found on PATH.",
            failure_class="transport_failure",
        )

    args = ["claude", "-p", "--output-format", "text", prompt]
    env = _sanitized_env("claude")

    try:
        result = subprocess.run(
            args,
            cwd=work_folder,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise AgentTransportError(
            f"Claude Code timed out after {timeout}s in {work_folder}.",
            failure_class="transport_failure",
        ) from exc

    return result.stdout


def _sanitized_env(agent: str) -> dict[str, str]:
    """Build a sanitized environment for subprocess launch.

    For Claude Code: strips all CLAUDE* env vars to prevent the nesting guard
    hang. Without this, `claude -p` detects it's inside an active session and
    hangs indefinitely.
    """
    env = os.environ.copy()
    if agent == "claude":
        for key in list(env):
            if key.startswith("CLAUDE"):
                del env[key]
    return env


def invoke_live_fp(
    target: Path,
    *,
    artifact_path: str,
    edge_name: str,
    judge: JudgeFn,
    archive: Optional[RunArchive] = None,
    model: str = "sonnet",
) -> LiveFpResult:
    """Invoke a real LLM via subprocess using the F_P dispatch contract.

    Architecture: F_D → subprocess → F_P (ADR-022)
    Transport: claude -p with CLAUDE* env vars stripped

    This is the prompt sufficiency test:
      1. Run iterate to get the real manifest
      2. Snapshot pre-existing artifact (setup may pre-seed for F_D checks)
      3. Send the manifest prompt via subprocess — nothing more
      4. Detect whether the LLM wrote a new artifact (mtime comparison)
      5. Run the deterministic judge as cross-check
      6. Ingest via assess-result protocol
      7. Check gaps for convergence

    The LLM receives ONLY what production guarantees.
    No hidden side channels. No extra instructions.

    On transport failure (timeout, pipe death, crash): returns a LiveFpResult
    with failure_class set instead of hanging or raising. The test can assert
    on failure_class to distinguish transport issues from quality issues.
    """
    assert _has_mcp_transport(), (
        "Claude Code CLI required for live F_P qualification"
    )

    label_prefix = "live-fp"

    # 1. Iterate → manifest
    iter_result = run_genesis(target, "iterate", archive=archive, label=f"{label_prefix} iterate")
    assert iter_result.returncode == 0, (
        f"iterate failed (exit {iter_result.returncode}):\n{iter_result.stderr}"
    )
    iter_data = json.loads(iter_result.stdout)
    assert "fp_manifest_path" in iter_data, "iterate must produce fp_manifest_path"

    manifest_path = Path(iter_data["fp_manifest_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # 2. Snapshot pre-existing artifact state (setup may have pre-seeded for F_D checks)
    art = target / artifact_path
    art.parent.mkdir(parents=True, exist_ok=True)
    pre_existed = art.exists()
    pre_mtime = art.stat().st_mtime if pre_existed else None

    # 3. Send exactly the manifest prompt via subprocess — nothing more
    prompt = manifest["prompt"]
    try:
        raw_response = _call_claude_code_mcp(prompt, str(target))
    except McpTransportError as exc:
        # Transport failure — archive what we have and return classified result
        if archive:
            archive._commands.append({
                "label": f"{label_prefix} claude -p [FAILED]",
                "args": ["claude", "-p", "--output-format", "text", "<prompt>"],
                "returncode": -1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(exc),
                "failure_class": exc.failure_class,
            })
            live_dir = archive.artifacts_dir / "live_fp"
            live_dir.mkdir(parents=True, exist_ok=True)
            (live_dir / "manifest.json").write_text(
                json.dumps(manifest, indent=2), encoding="utf-8")
            (live_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
            (live_dir / "transport_error.txt").write_text(str(exc), encoding="utf-8")

        return LiveFpResult(
            manifest=manifest, raw_response="", artifact_content="",
            model=model,
            judge_assessments=[{
                "evaluator": edge_name,
                "result": "fail",
                "evidence": f"transport_failure: {exc}",
            }],
            judge_passed=False, gaps_after={}, converged=False,
            failure_class=exc.failure_class,
        )

    # Archive the subprocess invocation
    if archive:
        archive._commands.append({
            "label": f"{label_prefix} claude -p",
            "args": ["claude", "-p", "--output-format", "text", "<prompt>"],
            "returncode": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    # 4. Read the artifact — detect whether the LLM wrote something new.
    #    Never fall back to a pre-seeded artifact; use raw_response if the LLM
    #    did not write to the expected path. This prevents self-seeding where
    #    setup artifacts pass the judge without the LLM having done any work.
    llm_wrote_new = (
        art.exists()
        and (not pre_existed or art.stat().st_mtime > pre_mtime)
    )
    if llm_wrote_new:
        artifact_content = art.read_text(encoding="utf-8")
        failure_class = None
    else:
        artifact_content = raw_response
        art.write_text(raw_response, encoding="utf-8")
        failure_class = "no_output" if not raw_response.strip() else None

    # 5. Run the deterministic judge
    assessments = judge(art, manifest)
    judge_passed = all(a["result"] == "pass" for a in assessments)
    if not judge_passed and failure_class is None:
        failure_class = "quality_failure"

    # 6. Write judge assessments via result_path protocol
    manifest_id = manifest_path.stem
    result_file = write_fp_result(
        target, manifest_id, edge_name, assessments,
        actor=f"live_fp_{model}",
    )
    r = assess_result(target, result_file, archive=archive)
    assert r.returncode == 0, f"assess-result failed:\n{r.stderr}"

    # 7. Check gaps
    gaps = run_genesis_json(target, "gaps", archive=archive, label=f"{label_prefix} gaps")

    # Archive the live run evidence
    if archive:
        live_dir = archive.artifacts_dir / "live_fp"
        live_dir.mkdir(parents=True, exist_ok=True)
        (live_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8")
        (live_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
        (live_dir / "raw_response.txt").write_text(raw_response, encoding="utf-8")
        (live_dir / "artifact.txt").write_text(artifact_content, encoding="utf-8")
        (live_dir / "judge_verdict.json").write_text(json.dumps({
            "passed": judge_passed,
            "assessments": assessments,
            "model": model,
            "transport": "subprocess:claude-p",
            "failure_class": failure_class,
        }, indent=2), encoding="utf-8")

    return LiveFpResult(
        manifest=manifest, raw_response=raw_response,
        artifact_content=artifact_content, model=model,
        judge_assessments=assessments, judge_passed=judge_passed,
        gaps_after=gaps, converged=gaps.get("converged", False),
        failure_class=failure_class,
    )
