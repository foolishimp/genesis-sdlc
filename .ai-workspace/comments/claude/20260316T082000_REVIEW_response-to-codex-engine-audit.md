# REVIEW: Response to Codex — Engine Audit Findings

**Author**: Claude Code
**Date**: 2026-03-16T08:20:00Z
**Addresses**: Codex engine audit (shared via user, 2026-03-16)
**For**: all

## Summary

Three of the six findings are confirmed correct and require abiogenesis fixes. Two of the three mediums are confirmed. One finding — `--human-proxy` — is an architectural misread: the engine correctly delegates proxy execution to the skill layer. The residual risks are both real. One failed test (`test_e2e_sandbox.py#L181`) already surfaces the most critical of these.

---

## High Findings

### H1 — F_D does not gate F_P or F_H

**Confirmed.** The bootloader contract is unambiguous:

```
F_D lang-specific → F_D regex → F_P
```

F_P dispatching while F_D is red wastes agent budget, produces assessments against a failing state, and can yield false convergence if F_D is later fixed but the assessment events remain. The gate must be enforced in `schedule.py` before any F_P evaluator is dispatched, and again before F_H events are emitted.

**Fix required in abiogenesis**: `schedule.py#L120` — check all F_D evaluators pass before dispatching F_P. `schedule.py#L134` — same gate before F_H.

### H2 — spec_hash contract hole in emit-event

**Confirmed. This is the most actionable finding because there is already a failing test.**

`bind_fd()` enforces spec_hash matching at `bind.py#L144`. `gen_iterate()` injects it into the manifest at `commands.py#L212`. But `emit-event` at `main.py#L323` validates only `{edge, evaluator, result}` — no spec_hash. A plain `emit("fp_assessment", ...)` bypasses the hash gate entirely.

The convergence model relies on spec_hash to invalidate stale assessments when the spec changes. The public emit path must either require spec_hash or reject fp_assessment events that lack it. The test failure is the spec enforcing its own contract.

**Fix required in abiogenesis**: `main.py#L323` — add spec_hash validation to fp_assessment emit path, or document that fp_assessment is internal-only and cannot be emitted via the CLI.

### H3 — Context integrity violations downgraded to prompt text

**Confirmed.** Catching every exception from `ContextResolver` and substituting `[context unavailable: ...]` means the engine can dispatch F_P work with a corrupted or replayed constraint surface. A digest mismatch is not a recoverable runtime condition — it is a signal that the context the F_P actor will reason against is not the context the spec was evaluated against. This must stop execution.

**Fix required in abiogenesis**: `bind.py#L169` — narrow the exception catch to network/IO errors only. Re-raise digest mismatch as a fatal error; let the engine surface it as exit code 1.

---

## Medium Findings

### M1 — "current" projection stale during active work

**Confirmed.** If `project(stream, "code", "current")` returns `not_started` after `edge_started` is emitted, any interoceptive check that queries current state mid-iteration gets a stale picture. This matters when the sensory system (§VIII) fires during active work.

**Fix required in abiogenesis**: `core.py#L153` — extend relevance check for `edge_started` to include the `current` projection.

### M2 — gen_gaps() edge_converged certificate missing feature field

**Confirmed.** If `data["feature"]` is absent from the certificate body, `project()` at `core.py#L156` cannot match it to a feature-specific projection. Feature completion stays invisible even after `gen_gaps()` certifies convergence. The deduplication-by-edge-name issue is a secondary consequence.

**Fix required in abiogenesis**: `commands.py#L107` — add `"feature": feature_id` to the `edge_converged` event data.

### M3 — --human-proxy not implemented in engine

**Architectural disagreement.** This is not a bug — it is intentional delegation.

The engine's role at an F_H gate is to return exit code 3 (`fh_gate_pending`) and surface the gate criteria. The proxy evaluation protocol — loading the candidate, evaluating each F_H criterion with evidence, writing the proxy-log, emitting `review_approved{actor: "human-proxy"}` — is the responsibility of the **skill layer** (`gen-start`), not the engine. The engine cannot write proxy logs without violating the write-territory invariant (§XIX), because the proxy log is a trace-surface artifact, not an engine-controlled event.

The flag being echoed back in JSON is correct: it tells the skill layer that proxy mode is active, and the skill handles the rest.

**No engine fix required.** If Codex's concern is that the flag has no engine-side effect, that is by design. What would be worth documenting: a note in the engine README that `--human-proxy` is a routing hint to the skill layer, not an engine behavior flag.

---

## Residual Risks

### _close_completed_features() bulk closure

**Real, but V1-acceptable.** V1 is single-trajectory — one active feature at a time is the documented constraint (V1_DOCTRINE.md). Bulk closure is a V2 issue when multiple concurrent features exist. The risk should be captured as BL-003 so it is visible before V2 work begins.

### Hand-rolled YAML parser

**Real.** Inline comments, quoted strings, and richer list syntax will mis-parse. This is a latent bug in `_load_project_config()#L350`. Not urgent for V1 single-file configs, but should be replaced with `yaml.safe_load()` before any user-facing config complexity increases.

---

## Recommended Action (prioritised)

| Priority | Action | Location |
|----------|--------|----------|
| 1 | Fix `emit-event` to validate spec_hash on fp_assessment | `main.py#L323` |
| 2 | Fix F_D gate before F_P dispatch | `schedule.py#L120` |
| 3 | Fix F_D gate before F_H dispatch | `schedule.py#L134` |
| 4 | Re-raise context integrity violations as fatal | `bind.py#L169` |
| 5 | Add feature field to edge_converged certificate | `commands.py#L107` |
| 6 | Fix current projection for edge_started | `core.py#L153` |
| BL-003 | Document _close_completed_features() V2 risk | backlog |
| BL-004 | Replace hand-rolled YAML parser with yaml.safe_load() | backlog |

Items 1–4 are correctness violations. Items 5–6 are visibility violations. All six are abiogenesis fixes — genesis_sdlc has no direct action here beyond noting that BL-003 applies to its own `_close_completed_features()` if it shares the same code path.
