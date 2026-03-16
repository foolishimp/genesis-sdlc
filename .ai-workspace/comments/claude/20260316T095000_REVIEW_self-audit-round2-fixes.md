# REVIEW: Self-Audit — Round 2 Fixes

**Author**: Claude Code
**Date**: 2026-03-16T09:50:00Z
**Addresses**: commits 40d1209 and 3ee4e7e — engine correctness rounds 1 and 2
**For**: all

## Summary

Seven findings. Two are critical regressions introduced by my own fixes. Two are
high-severity gaps that were not in scope before. Three are medium/low. This document
is the result of reading the code as an adversarial reviewer, not as the author.

---

## Critical Findings (my own regressions)

### C1 — gen_start auto-loop infinite-loops on mixed F_D+F_P failure

`gen_start` detects fd_gap by checking for `fd_gap_found` in new stream events at
`commands.py#L314`:

```python
if "fd_gap_found" in new_types:
    result["stopped_by"] = "fd_gap"
    return result
```

My gen_iterate() early return (H1 fix) emits zero events — no `fd_gap_found` in the
stream. `new_types` is empty. The fd_gap condition is never triggered. The loop runs
all 50 iterations returning the same early result each time, then exits with
`stopped_by: "max_iterations"` instead of `"fd_gap"`.

The existing test (`test_auto_loop_stops_on_fd_gap`) uses a pure-F_D package with no
F_P evaluators. That test path does not take the early return — it goes through
`schedule.iterate()` which emits `fd_gap_found`. The mixed F_D+F_P case is not tested.

**Root cause**: I applied the gate at the wrong layer. `gen_iterate()` should emit
`fd_gap_found` before returning early, so `gen_start`'s event-based detection works.
OR: `gen_start` should also check `result.get("stopped_by") == "fd_gap"` directly.
The event-based detection is the existing contract — the fix is to emit `fd_gap_found`
in the early return path.

### C2 — gen-start skill broken by REQ-F-EVAL-004

The gen-start skill's Step 3 emits fp_assessment without spec_hash:

```bash
PYTHONPATH=.genesis python -m genesis emit-event \
  --type fp_assessment \
  --data '{"edge": "{edge}", "evaluator": "{evaluator}", "result": "pass"}'
```

REQ-F-EVAL-004 makes this fail: `emit-event` now requires `spec_hash` for fp_assessment.
Every gen-start invocation in every workspace fails at the fp_assessment emit step.
`manifest["spec_hash"]` is available in Step 3 — the skill just doesn't read it.

This would have been caught immediately if I had run gen-start against a real workspace
after the fix. The self-hosting test runs `genesis gaps`, not `genesis start`.

---

## High Findings (new gaps)

### H1 — EVAL-005 guards emit() but stream.append() is the real write path

`emit()` validation is bypassed by `stream.append()`. The test at
`test_e2e_domain_blind.py#L385` calls `ws.append("fp_assessment", {...})` without
spec_hash and passes. The `emit()` docstring says it is "the ONLY admissible write to
events.jsonl" — but `stream.append()` is a public method and nothing enforces this.

The EVAL-005 fix hardens the API surface that external callers see, but the same hole
exists at the stream layer. Any in-process code that accesses the EventStream directly
(including tests) can write stale assessments.

Fix options: make `EventStream.append()` validate fp_assessment payloads the same way
`emit()` does, OR document that `stream.append()` is a test-only bypass and flag the
domain_blind test as using the opt-out path.

### H2 — gen_iterate early return is inconsistent with pure-F_D path

Pure F_D failure: edge_started IS emitted, fd_gap_found IS emitted, events_emitted=2.
Mixed F_D+F_P failure: early return, NO edge_started, NO fd_gap_found, events_emitted=0.

Two callers doing the same thing (fixing a broken edge) get different event stream traces.
This affects observability, replay, and any interoceptive system that watches for
edge_started or fd_gap_found. The self-hosting test does not cover the mixed case.

---

## Medium Findings

### M1 — emit() accepts spec_hash=None as a valid payload

The EVAL-005 check is `"spec_hash" not in data`. A caller passing `{"spec_hash": None}`
passes the check but produces an event that bind_fd() will never match (since
`e.get("data", {}).get("spec_hash") == "real_hash"` is `None == "real_hash"` → False).
The event is accepted but silently fails to converge. Should validate that
`spec_hash is not None` and is a non-empty string.

### M2 — co_evolve edge target covers only one of two co-evolved assets

`code↔unit_tests` has `target=unit_tests`. My edge_started fix (H2) filters by target,
so `project(stream, "code", "current")` never observes the edge_started for this edge.
During TDD iteration, the code current projection stays "not_started" even though the
edge is active. The unit_tests projection correctly shows "in_progress".

For V1 single-trajectory this is benign — no interoceptive system currently queries
project() for "current". But it is an incorrect projection.

### M3 — delta() spec_hash=None opt-out is undocumented

`delta()` in schedule.py takes `spec_hash: str | None = None`. Passing None opts out of
snapshot binding: all fp_assessment events pass regardless of their spec_hash. Many
tests use this path. There is no documentation about when callers should use None vs a
real hash, and `spec_hash=None` is now in tension with EVAL-004/EVAL-005 which make
spec_hash mandatory on the emit path.

---

## Recommended Fixes (prioritised)

| Priority | Fix | Location |
|----------|-----|----------|
| 1 | Emit `fd_gap_found` in gen_iterate() early return, OR check result["stopped_by"] in gen_start auto-loop | `commands.py` |
| 2 | Update gen-start skill to include spec_hash from manifest in emit-event call | `CLAUDE.md` / gen-start skill |
| 3 | Validate spec_hash is not None in emit() | `core.py` |
| 4 | Document stream.append() as test-only bypass; flag domain_blind test | `test_e2e_domain_blind.py` |
| 5 | Test gen_start auto-loop with mixed F_D+F_P failure | `test_e2e_sandbox.py` or `test_commands.py` |
