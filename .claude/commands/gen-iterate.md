# /gen-iterate — Run One Iteration Cycle

Runs one F_D→F_P→F_H cycle on a single feature+edge. The engine selects the
next unconverged edge. This skill manages only the MCP handoff.

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
| 2 | fp_dispatched | MCP dispatch (Step 3) |
| 3 | fh_gate_pending | F_H evaluation — proxy or wait (Step 5) |
| 4 | fd_gap | F_D still failing after F_P resolved — surface failures, stop (Step 4) |
| 5 | max_iterations | Loop limit hit — report to user, stop |

**Step 3 — MCP dispatch (exit code 2 only)**

```
manifest_path = output["fp_manifest_path"]
manifest = read(manifest_path)
```

Call `mcp__claude-code-runner__claude_code` with:
- `prompt`: manifest["prompt"]
- `workFolder`: workspace root

The actor writes its assessment JSON to `manifest["result_path"]`.

**After MCP returns**, the skill reads `result_path` and emits `fp_assessment` for each
passing evaluator (F_P actors do NOT call emit-event — the skill is the F_D-controlled
write path per GENESIS_BOOTLOADER §V):

```
result = read_json(manifest["result_path"])   # {edge, assessments: [{evaluator, result, evidence}]}
for assessment in result["assessments"]:
  if assessment["result"] == "pass":
    PYTHONPATH=.genesis python -m genesis emit-event \
      --type fp_assessment \
      --data '{"edge": "{edge}", "evaluator": "{evaluator}", "result": "pass"}'
```

Go to Step 1.

**Step 4 — fd_gap (exit code 4 only)**

F_D checks are still failing after F_P construction was resolved. The F_P actor already
wrote its assessment (fp_assessment pass event exists in the stream) but the deterministic
checks still fail. This is a construction quality problem — do NOT re-dispatch F_P.

Surface the F_D failures verbatim from `output["failing_evaluators"]` and the delta summary.
Stop. The operator must inspect and fix the underlying deterministic failure before iterating again.

## F_H Gate (exit code 3)

Surface the gate output to the user verbatim.

**Standard path**: Wait for human decision.
- On approval: emit `review_approved` event, then go to Step 1:
  ```bash
  PYTHONPATH=.genesis python -m genesis emit-event \
    --type review_approved \
    --data '{"feature": "{F}", "edge": "{E}", "actor": "human"}'
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
     --type review_approved \
     --data '{"feature": "{F}", "edge": "{E}", "actor": "human-proxy", "proxy_log": "{path}"}'
   ```
6. On rejection: emit `review_rejected` with `actor: "human-proxy"`. Stop. Do not retry
   this edge in the same session.
