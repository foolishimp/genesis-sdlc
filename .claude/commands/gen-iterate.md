# /gen-iterate — Invoke the Universal Iteration Function

<!-- Implements: REQ-ITER-001, REQ-ITER-002, REQ-UX-004 -->
<!-- Design: ADR-032 (skills as dispatch surfaces) -->

Run one F_D→F_P→F_H cycle on a feature+edge. The engine manages state,
events, and convergence. This skill manages only the MCP handoff.

## Usage

```
/gen-iterate [--feature REQ-F-*] [--edge "source→target"]
```

## Instructions

**Step 1 — Run the engine**

```bash
PYTHONPATH=.genesis python -m genesis start \
  [--feature {feature}] [--edge {edge}]
```

Parse stdout as JSON.

**Step 2 — Route on exit code**

| Exit | Status | Action |
|------|--------|--------|
| 0 | converged / nothing_to_do | Done. Report result to user. |
| 2 | fp_dispatched | MCP dispatch (Step 3) |
| 3 | fh_required | Surface gate to user. Wait. |
| 1 | error | Report error. Stop. |

**Step 3 — MCP dispatch (exit code 2 only)**

```
manifest_path = output["fp_manifest_path"]
manifest = read(manifest_path)
```

Call `mcp__claude-code-runner__claude_code` with:
- `prompt`: manifest["prompt"]
- `workFolder`: workspace root

The actor reads its mandate from the manifest, does the construction work
(read files, write code, run tests), and writes its result to
`manifest["result_path"]`.

re-run the engine (go to Step 1). The engine finds the fold-back result and re-evaluates.

## Exit Protocol

Exit code 2 is the only in-skill logic. Everything else is the engine.
The engine emits all events. The engine detects convergence.
The skill's sole responsibility is the MCP tool call the engine cannot make.

## Output Artifacts

The engine updates these derived views after each iteration:
- **`events.jsonl`** — append-only event log (`event_type`, timestamp, feature, edge, data)
- **`STATUS.md`** — derived view of feature vector status (reconstructed from events)
- **`ACTIVE_TASKS.md`** — TASK LOG filtered projection of convergence events
- **feature vector YAML** — trajectory and status updated per edge result

All three views are derived from events alone. The event log is the source of truth.

## Convergence Exit Codes (exit 0 subcases)

| Subcase | Constant | Meaning |
|---------|----------|---------|
| delta = 0 | `CONVERGED` | All evaluators passed |
| question resolved | `CONVERGED_QUESTION_ANSWERED` | Discovery/spike: question answered |
| time box expired | `TIME_BOX_EXPIRED` | Graceful fold-back of partial results |

## Fold-Back Protocol (exit code 2 detail)

The engine signals `FpActorResultMissing` when F_P construction is required but
no actor result exists. Exit code 2 carries `fp_manifest_path` pointing to a
pending `fp_intent_{run_id}.json` manifest.

Three-party contract: **ENGINE** writes the manifest → **LLM** (this skill) reads
it and dispatches the **ACTOR** via MCP → ACTOR writes `fp_result_{run_id}.json`
to `result_path` → ENGINE re-evaluates.

Manifest schema (status transitions from `pending` → `dispatched` after actor
is invoked, preventing double-dispatch on session resume — ADR-023):
```json
{
  "run_id": "...",
  "prompt": "...",
  "result_path": ".ai-workspace/agents/fp_result_{run_id}.json",
  "status": "pending"
}
```

Actor result schema (written to `result_path`):
```json
{
  "converged": true,
  "delta": 0,
  "cost_usd": 0.042
}
```

Deduct `cost_usd` from remaining `budget_usd` for budget tracking.

**Constraint (ADR-023)**: No subprocess spawning, no `claude -p`. MCP is the
only invocation path. The skill's sole responsibility is the MCP tool call the
engine cannot make.

## F_H Gate and Human Proxy Mode

**If human evaluator required** (exit code 3):

**Standard path**: Surface the gate output to user verbatim. Wait for approval.
- On approval: `review_approved` event with `actor: "human"`
- On rejection: stop. Report to user.

**If human-proxy mode is active** (`--human-proxy` flag — session only, never persisted):

Proxy evaluation protocol (per-criterion):
1. Load the candidate artifact and the F_H criteria for this edge
2. For each F_H criterion, evaluate with explicit evidence from the artifact:
   - `Criterion`: name of the check
   - `Evidence`: specific text or observation from the artifact
   - `Satisfied`: yes/no with reasoning
3. Decision: `approved` if every required F_H criterion is satisfied; `rejected` if any required criterion fails
4. Do not introduce additional standards beyond those defined in the edge evaluators — only evaluates defined criteria

**Proxy log** — write to `.ai-workspace/reviews/proxy-log/{ISO}_{feature}_{edge}.md` BEFORE emitting any event.
The proxy-log directory is auto-created if absent.

Required proxy-log fields:
```
Feature: REQ-F-*
Edge: source→target
Iteration: N
Timestamp: ISO 8601
Decision: approved | rejected

Criteria:
- Criterion: human_validates_completeness
  Evidence: [specific evidence from artifact]
  Satisfied: yes | no
  Reasoning: [why]

Summary: [overall reasoning]
```

If the session is interrupted before the log is written, the log entry is incomplete.
Incomplete proxy-log entries are reported at the next session start for morning review.

**Event emission**:
- Approval: emit `review_approved` with `actor: "human-proxy"` and `proxy_log: "{path}"`
- Rejection: emit `review_rejected` with `actor: "human-proxy"`

**Actor field invariant**: `actor: "human"` on standard path; `actor: "human-proxy"` on proxy path.
Both paths always set the actor field on `review_approved` events.
Existing `review_approved` events without an actor field are treated as `actor: "human"` (backward compatibility).

**Rejection halt**: On rejection, emit `PROXY REJECTION` report identifying:
- Feature: REQ-F-*
- Edge: source→target
- Criterion: which criterion failed
- Evidence: what was found

Set feature status to `iterating`. Do not retry this edge in the same session (self-correction prohibited after rejection). Other features are unaffected and the loop continues.

## Auto-selection from Context

When `--feature` or `--edge` is not provided, the engine auto-selects:

1. Reads `.ai-workspace/features/active/` to discover active feature vectors
2. Ranks by recency — feature with the most recent event is selected first
3. Determines the next non-converged edge from the graph topology
4. Falls back to prompting if context is ambiguous (multiple features at same
   recency, or no active features)

## Evaluator Detail

When a required check fails, the engine emits an `evaluator_detail` event per failed check.
This enables stuck delta detection: if the same check fails 3+ iterations in a row,
a `stuck delta` pattern is detected and an `intent_raised` event is emitted.
