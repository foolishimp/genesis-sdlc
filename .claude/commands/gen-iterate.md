# /gen-iterate — Run One Iteration Cycle

Runs one F_D→F_P→F_H cycle on a single feature+edge. The engine selects the
next unconverged edge. This skill manages only the F_P handoff.

Use `/gen-start --auto` to loop. Use `/gen-iterate` for a single controlled step.

## Usage

```
/gen-iterate [--feature REQ-F-*] [--edge "source→target"]
```

## Instructions

**Step 1 — Run the engine**

```bash
PYTHONPATH=.genesis python -m genesis iterate \
  [--feature {F}] [--edge {E}]
```

Parse stdout as JSON.

**Step 2 — Route on exit code**

| Exit | Status | Action |
|------|--------|--------|
| 0 | converged / nothing_to_do | Done. Report to user. |
| 1 | error | Report error. Stop. |
| 2 | fp_dispatched | F_P dispatch (Step 3) |
| 3 | fh_gate_pending | F_H evaluation — proxy or wait (Step 5) |
| 4 | fd_gap | F_D still failing after F_P resolved — surface failures, stop (Step 4) |
| 5 | max_iterations | Loop limit hit — report to user, stop |

**Step 3 — F_P dispatch via canonical transport (exit code 2 only)**

```
manifest_path = output["fp_manifest_path"]
manifest = read(manifest_path)
```

Dispatch via the engine's transport wrapper:

```python
from genesis.fp_dispatch import call_agent

call_agent(manifest["prompt"], workspace_root)
```

`call_agent` handles agent selection, environment sanitization, and timeout (ADR-022).
Do NOT restate transport details (CLI flags, env var stripping) — the wrapper owns that.

The actor writes its assessment JSON to `manifest["result_path"]`.

**After the agent returns**, ingest the result via the engine's assess-result command.
This resolves manifest provenance (spec_hash, workflow_version) and emits assessed
events — the skill must NOT emit events directly:

```bash
PYTHONPATH=.genesis python -m genesis assess-result \
  --result "$(echo $manifest | jq -r .result_path)" \
  --workspace .
```

Go to Step 1.

**Step 4 — fd_gap (exit code 4 only)**

F_D checks are still failing after F_P construction was resolved. The F_P actor already
wrote its assessment (assessed pass event exists in the stream) but the deterministic
checks still fail. This is a construction quality problem — do NOT re-dispatch F_P.

Surface the F_D failures verbatim from `output["failing_evaluators"]` and the delta summary.
Stop. The operator must inspect and fix the underlying deterministic failure before iterating again.

## F_H Gate (exit code 3)

Surface the gate output to the user verbatim.

**Standard path**: Wait for human decision.
- On approval: emit `approved` event, then go to Step 1:
  ```bash
  PYTHONPATH=.genesis python -m genesis emit-event \
    --type approved \
    --data '{"kind": "fh_review", "feature": "{F}", "edge": "{E}", "actor": "human"}'
  ```
- On rejection: stop. Report to user.

**Proxy path** (`--human-proxy` flag supplied to this invocation):
1. Load the candidate artifact and the F_H criteria for this edge
2. For each F_H criterion, evaluate with explicit evidence:
   - `Criterion`: name of the check
   - `Evidence`: specific text or observation from the artifact
   - `Satisfied`: yes/no with reasoning
3. Decision: `approved` if every required criterion passes; `rejected` if any fail
4. Write proxy-log to `.ai-workspace/reviews/proxy-log/{ISO}_{feature}_{edge}.md` BEFORE emitting:
   ```
   Feature: {F}
   Edge: {E}
   Iteration: N
   Timestamp: ISO 8601
   Decision: approved | rejected

   Criteria:
   - Criterion: ...
     Evidence: ...
     Satisfied: yes | no
   ```
5. On approval: emit event, then go to Step 1:
   ```bash
   PYTHONPATH=.genesis python -m genesis emit-event \
     --type approved \
     --data '{"kind": "fh_review", "feature": "{F}", "edge": "{E}", "actor": "human-proxy", "proxy_log": "{path}"}'
   ```
6. On rejection: emit `assessed` with `kind: fh_review, result: reject, actor: "human-proxy"`. Stop. Do not retry
   this edge in the same session.

## Edge-Specific Constraints

### F_D evaluator acyclicity (all edges)

F_D evaluator `command:` fields MUST NOT invoke `genesis` subcommands or run tests that do.
Violation causes unbounded subprocess recursion. When authoring evaluators:
- `pytest -m 'not e2e'` — correct (excludes e2e tests that call genesis)
- `pytest` with no marker — incorrect if any e2e test invokes genesis commands
- Any `genesis gaps|start|iterate` call — incorrect (cyclic)

### `user_guide→uat_tests` edge

The F_H gate for this edge requires **sandbox e2e evidence** and a **current user guide**
before approval is granted. The upstream `unit_tests→integration_tests` edge produces the
sandbox report; the `integration_tests→user_guide` edge certifies the guide.

`--human-proxy` may proxy this gate only if:
1. `sandbox_report.json` shows `all_pass: true`
2. `USER_GUIDE.md` is version-current and REQ-coverage-tagged

A proxy approval without both is a log-integrity violation.

Unit tests alone (`code↔unit_tests`) are necessary but not sufficient.
**Shipping requires sandbox proof and a current guide.**
