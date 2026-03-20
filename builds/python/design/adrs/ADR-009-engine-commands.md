# ADR-009: Engine Commands (gen-gaps, gen-iterate, gen-start)

**Status**: Accepted
**Date**: 2026-03-21
**Implements**: REQ-F-CMD-001, REQ-F-CMD-002, REQ-F-CMD-003

## Context

The SDLC graph defines assets, edges, and evaluators — but the operator needs commands to drive the convergence engine. Three commands form the operator interface.

## Decision

### gen-gaps (REQ-F-CMD-001)

Reports delta per edge. Returns JSON: `total_delta`, `converged`, `gaps[]` with per-job `edge`, `delta`, `failing`, `passing`, `delta_summary`. Runs all F_D evaluators as subprocesses, projects F_H and F_P from the event stream. `converged: true` iff `total_delta == 0`.

### gen-iterate (REQ-F-CMD-002)

One bind-and-iterate pass. Selects first unconverged job in topological order. Calls `bind_fd()` to pre-compute all evaluator states. Enforces F_D→F_P→F_H ordering:

| Condition | Exit code | Action |
|-----------|-----------|--------|
| F_D failing | 4 (fd_gap) | Report failures, stop |
| F_P needed | 2 (fp_dispatched) | Write manifest to `.ai-workspace/fp_manifests/`, stop |
| F_H needed | 3 (fh_gate_pending) | Report criteria, stop |
| Converged | 0 | Done |

### gen-start (REQ-F-CMD-003)

State-machine entry. `--auto` loops gen-iterate up to MAX_AUTO (50), stopping on convergence, fp_dispatched, fh_gate_pending, fd_gap, or max iterations. `--human-proxy` requires `--auto` — evaluates F_H gates per proxy protocol.

## Tech Stack

Commands implemented in abiogenesis engine (`genesis/commands.py`). genesis_sdlc installs them as slash commands via `.claude/commands/`. The Package defines the graph; the engine provides the commands.

## Consequences

- Commands are engine-level, not package-level — a non-SDLC package gets the same commands
- Exit codes are the API contract between the engine and the `/gen-start` skill
- F_D→F_P→F_H ordering is structural, not configurable
