# Implements: REQ-F-CORE-004
"""
bind — F_D pre-computation: bind_fd, bind_fp, select_relevant_contexts,
       render_delta.

The linker: turns a typed GTL skeleton into an F_P-executable manifest.
Phase 3 of the approved execution plan. See ADR-002, ADR-003.

bind_fd  — deterministic, no LLM required. Produces PrecomputedManifest.
bind_fp  — assembles F_P manifest from pre-computed material. Also F_D.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from gtl.core import Context, Evaluator, F_D, F_H, F_P, Job

from .core import ContextResolver, EventStream, project
from .manifest import BoundJob, PrecomputedManifest


# ── F_D evaluator runner ──────────────────────────────────────────────────────

def run_fd_evaluator(
    ev: Evaluator,
    current_asset: dict,
    workspace_root: Path,
) -> tuple[bool, Any]:
    """
    Run one F_D evaluator. Returns (passes: bool, detail: Any).

    Dispatches via ev.command — the Package specifies; the kernel runs.
    Fails closed: an F_D evaluator with no command is a misconfigured Package.
    PYTHONPATH is set so genesis and gtl packages resolve inside the subprocess.
    """
    if ev.category is not F_D:
        raise TypeError(
            f"run_fd_evaluator called on non-F_D evaluator: {ev.name!r} "
            f"(category={ev.category.__name__})"
        )
    if not ev.command:
        return False, {
            "status": "error",
            "reason": f"F_D evaluator {ev.name!r} has no command — misconfigured Package",
        }

    # Propagate sys.path as PYTHONPATH so genesis/gtl are importable in subprocesses.
    env = os.environ.copy()
    extra = os.pathsep.join(p for p in sys.path if p)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [extra, existing]))

    result = subprocess.run(
        ev.command, shell=True, cwd=workspace_root,
        capture_output=True, text=True, env=env,
    )
    return result.returncode == 0, {
        "returncode": result.returncode,
        "stdout": result.stdout[-3000:],
        "stderr": result.stderr[-500:],
    }


# ── bind_fd ───────────────────────────────────────────────────────────────────

def bind_fd(
    job: Job,
    stream: EventStream,
    resolver: ContextResolver,
    workspace_root: Path,
) -> PrecomputedManifest:
    """
    F_D pre-computation phase. Everything computable without an LLM.

    Produces the residual gap — the minimal surface F_P must address.
    See ADR-002 for the split rationale.
    """
    # 1. Project current asset state
    source = job.source_type
    source_name = source[0].name if isinstance(source, list) else source.name
    current = project(stream, source_name, "current")

    # 2. Run all F_D evaluators — always, unconditionally.
    # edge_converged events are audit records (emitted by gen_gaps when delta=0),
    # not gates that bypass evaluation. F_D is deterministic; re-running is cheap
    # and necessary for live convergence detection.
    all_events = stream.all_events()
    fd_results: dict[str, Any] = {}
    for ev in job.evaluators:
        if ev.category is F_D:
            passes, detail = run_fd_evaluator(ev, current, workspace_root)
            fd_results[ev.name] = {"passes": passes, "detail": detail}

    def _passes(ev: Evaluator) -> bool:
        if ev.category is F_D:
            return fd_results.get(ev.name, {}).get("passes", False)
        if ev.category is F_H:
            # Resolved if review_approved event exists for this edge
            return any(
                e.get("event_type") == "review_approved"
                and e.get("data", {}).get("edge") == job.edge.name
                for e in all_events
            )
        if ev.category is F_P:
            # Resolved if fp_assessment with result=pass exists for this evaluator+edge
            return any(
                e.get("event_type") == "fp_assessment"
                and e.get("data", {}).get("edge") == job.edge.name
                and e.get("data", {}).get("evaluator") == ev.name
                and e.get("data", {}).get("result") == "pass"
                for e in all_events
            )
        return False

    failing = [ev for ev in job.evaluators if not _passes(ev)]
    passing = [ev for ev in job.evaluators if _passes(ev)]

    # 4. Select relevant contexts (F_D filters to what the gap actually needs)
    relevant_ctxs = select_relevant_contexts(job.edge.context, failing)
    resolved: dict[str, str] = {}
    for ctx in relevant_ctxs:
        try:
            resolved[ctx.name] = resolver.load(ctx)
        except (NotImplementedError, Exception) as exc:
            resolved[ctx.name] = f"[context unavailable: {exc}]"

    # 5. Build structured delta summary
    summary = render_delta(fd_results, failing)

    return PrecomputedManifest(
        job=job,
        current_asset=current,
        failing_evaluators=failing,
        passing_evaluators=passing,
        fd_results=fd_results,
        relevant_contexts=resolved,
        delta_summary=summary,
    )


# ── bind_fp ───────────────────────────────────────────────────────────────────

def bind_fp(
    pre: PrecomputedManifest,
    job: Job,
    result_path: str = "",
) -> BoundJob:
    """
    Assemble the minimal F_P manifest from pre-computed material.

    This function itself is F_D — template assembly only, no LLM.
    See ADR-003 for manifest structure.
    """
    prompt = _assemble_prompt(pre, job, result_path)
    return BoundJob(job=job, precomputed=pre, prompt=prompt, result_path=result_path)


def _assemble_prompt(pre: PrecomputedManifest, job: Job, result_path: str = "") -> str:
    """
    Assemble the F_P prompt.

    Structure: INVARIANTS → CURRENT STATE → GAP → RELEVANT CONTEXT → OUTPUT CONTRACT.
    F_P receives only what it needs to address the gap. Nothing more.
    """
    sections: list[str] = []

    # [INVARIANTS] — always present
    sections.append(
        "[INVARIANTS]\n"
        "- Assets are projections of the event stream — never mutate state directly.\n"
        "- emit() is the only write path. event_time is system-assigned.\n"
        "- Implement only V1 features. No V2 (spawn, consensus, release, multi-tenant).\n"
        "- All code files must carry: # Implements: REQ-* tags.\n"
        "- All test files must carry: # Validates: REQ-* tags.\n"
        "- Exactly 6 modules: core, bind, schedule, manifest, commands, __main__."
    )

    # [CURRENT STATE]
    src = job.edge.source
    src_name = " × ".join(a.name for a in src) if isinstance(src, list) else src.name
    sections.append(
        f"[CURRENT STATE]\n"
        f"Edge: {job.edge.name}\n"
        f"Source asset: {src_name}\n"
        f"Target asset: {job.edge.target.name}\n"
        f"Status: {pre.current_asset.get('status', 'unknown')}\n"
        f"Edges converged: {pre.current_asset.get('edges_converged', [])}"
    )

    # [GAP]
    gap_lines = [f"[GAP] — {len(pre.failing_evaluators)} evaluator(s) failing:"]
    for ev in pre.failing_evaluators:
        detail = pre.fd_results.get(ev.name, {})
        gap_lines.append(f"  {ev.name} ({ev.category.__name__}): {ev.description}")
        if detail:
            gap_lines.append(f"    F_D result: {detail.get('detail', detail)}")
    if not pre.failing_evaluators:
        gap_lines.append("  (none — all evaluators pass)")
    sections.append("\n".join(gap_lines))

    # [RELEVANT CONTEXT]
    if pre.relevant_contexts:
        ctx_lines = ["[RELEVANT CONTEXT]:"]
        for name, content in pre.relevant_contexts.items():
            # Cap each context to avoid overwhelming the F_P actor
            snippet = content[:4000] + ("…[truncated]" if len(content) > 4000 else "")
            ctx_lines.append(f"\n--- {name} ---\n{snippet}")
        sections.append("\n".join(ctx_lines))

    # [OUTPUT CONTRACT]
    target = job.edge.target
    fp_failing = [ev for ev in pre.failing_evaluators if ev.category is F_P]
    emit_lines = []
    for ev in fp_failing:
        emit_lines.append(
            f'  PYTHONPATH=.genesis python -m genesis emit-event \\\n'
            f'    --type fp_assessment \\\n'
            f'    --data \'{{"edge": "{job.edge.name}", "evaluator": "{ev.name}", "result": "pass"}}\''
        )
    emit_section = (
        "\n\nAfter completing your work, emit one fp_assessment per passing F_P evaluator:\n"
        + "\n".join(emit_lines)
    ) if emit_lines else ""

    sections.append(
        f"[OUTPUT CONTRACT]\n"
        f"Produce: {target.name} asset\n"
        f"Satisfying markov conditions: {target.markov}\n"
        f"Evaluators to pass: {[ev.name for ev in pre.failing_evaluators]}"
        + (f"\nWrite output to: {result_path}" if result_path else "")
        + emit_section
    )

    return "\n\n".join(sections)


# ── select_relevant_contexts ──────────────────────────────────────────────────

def select_relevant_contexts(
    all_contexts: list[Context],
    failing: list[Evaluator],
) -> list[Context]:
    """
    F_D: filter contexts to those relevant to the failing evaluators.

    Domain-blind: contexts are only needed when F_P work is required.
    F_D and F_H failures do not need prompt context — F_D re-runs its command,
    F_H waits for a review_approved event. Only F_P dispatch consumes context.
    """
    if not failing:
        return []
    fp_failing = [ev for ev in failing if ev.category is F_P]
    if not fp_failing:
        return []
    return list(all_contexts)


# ── render_delta ─────────────────────────────────────────────────────────────

def render_delta(
    fd_results: dict[str, Any],
    failing: list[Evaluator],
) -> str:
    """Render a structured human-readable gap description."""
    if not failing:
        return "delta = 0 — all evaluators pass"

    lines = [f"delta = {len(failing)} — {len(failing)} evaluator(s) failing:"]
    for ev in failing:
        detail = fd_results.get(ev.name, {})
        det = detail.get("detail", detail) if isinstance(detail, dict) else detail
        lines.append(f"  {ev.name} ({ev.category.__name__}): {det}")

    return "\n".join(lines)
