# /gen-start — State-Driven Routing Entry Point

<!-- Implements: REQ-UX-001, REQ-UX-002, REQ-UX-004, REQ-UX-005, REQ-TOOL-003 -->
<!-- Implements: REQ-INTENT-001, REQ-INTENT-002 -->
<!-- Design: ADR-032 (skills as dispatch surfaces) -->

State machine controller. Detects project state (derived from workspace — never stored),
selects the next work unit, runs the engine, handles F_P dispatch. The engine owns all
logic and events. This skill owns only the MCP handoff.

## Usage

```
/gen-start [--auto] [--human-proxy] [--feature REQ-F-*] [--edge "source→target"]
```

| Flag | Effect |
|------|--------|
| `--auto` | Loop through all pending targets until converged or blocked |
| `--human-proxy` | Evaluate F_H gates as proxy (requires `--auto`) |
| `--feature` | Override feature selection |
| `--edge` | Override edge selection |

## Instructions

### State Machine (engine-computed — pure read, never stored)

The engine reads the workspace and derives one of 8 states:

| State | Condition | Action |
|-------|-----------|--------|
| `UNINITIALISED` | No `.ai-workspace/` | **Progressive Init** — scaffold workspace |
| `NEEDS_CONSTRAINTS` | Unresolved mandatory constraints | **Constraint Prompting** — gather dimensions |
| `NEEDS_INTENT` | No intent document | **Intent Authoring** — write INTENT.md |
| `NO_FEATURES` | Intent but no feature vectors | **Feature Creation** — run /gen-iterate on requirements→feature_decomposition |
| `IN_PROGRESS` | Active features with unconverged edges | **Feature/Edge Selection** — iterate closest-to-complete |
| `ALL_CONVERGED` | All required features converged | **Release/Gaps** — run /gen-gaps, then /gen-release |
| `ALL_BLOCKED` | Nothing iterating, all blocked | **Blocked Recovery** — disposition blocked vectors |
| `STUCK` | δ unchanged 3+ iterations | **Stuck Recovery** — escalate or spawn |

State is derived from workspace artifacts on every invocation — it is never stored.

### Progressive Init (UNINITIALISED state)

When the workspace does not exist, the engine prompts for 5 inputs then scaffolds:

| # | Input | Auto-detect |
|---|-------|-------------|
| 1 | Project name | Directory name |
| 2 | Project kind | `package.json` → app; `pyproject.toml` → library |
| 3 | Language | Detected from config files |
| 4 | Test runner | `pytest`/`jest`/`cargo test` from config |
| 5 | Intent description | First line of INTENT.md if present |

Project kind maps to default profile:
- `application` → `standard` profile
- `library` → `standard` profile
- `poc` / `spike` → `poc` / `spike` profile

### Deferred Constraint Prompting (NEEDS_CONSTRAINTS state)

Mandatory constraint dimensions (ecosystem, deployment target, security model, etc.)
are deferred to the `requirements→design` edge — not collected at init time.
At the design gate, the engine surfaces unresolved dimensions and prompts sequentially.

### Feature/Edge Selection Algorithm (IN_PROGRESS state)

The engine selects the next work unit by topological walk:

**Priority tiers** (highest first):
1. **time-box expiring** — features approaching their time-box deadline
2. **closest-to-complete** — fewest unconverged edges remaining
3. **priority** — explicit priority field in feature vector
4. **recently touched** — last `iteration_completed` event timestamp

For the selected feature, edge determination walks the profile's graph from
the first unconverged edge in topological order (respecting dependencies).
Co-evolution edges (`code↔unit_tests`) are presented as a single unit.

User override: `--feature` and `--edge` bypass auto-selection.

### Auto Mode (--auto flag)

`--auto` loops the state machine until:
- All features converged (exit 0)
- **Human gate** required (exit 3 — surfaces F_H criteria, waits for approval)
- **Spawn** decision needed (exit 3 — presents proposal, waits)
- **Stuck** detected (exit 3 — escalates, waits)
- **Time-box** expired (exit 3 — surfaces for disposition)
- Error (exit 1)

### Recovery Scenarios (STUCK / corrupted workspace)

The engine detects and handles workspace anomalies non-destructively — never silently deleting:

| Scenario | Detection | Action |
|----------|-----------|--------|
| Corrupted event log | JSON parse failure | Flag lines, offer repair |
| Missing feature vectors | vector referenced in events but file absent | Warn, offer regeneration |
| Orphaned spawns | child vector with no parent | List orphans, request disposition |
| Stuck features | δ unchanged 3+ iterations | Escalate to human gate or spawn |

### Dispatch to /gen-iterate

For `IN_PROGRESS` state, the engine resolves feature and edge then invokes
`/gen-iterate --feature {F} --edge {E}`. The skill is the dispatch surface;
gen-iterate is the universal iteration function.

---

### Engine Execution

**Step 1 — Run the engine**

```bash
PYTHONPATH=.genesis python -m genesis start \
  [--auto] [--human-proxy] [--feature {F}] [--edge {E}]
```

Parse stdout as JSON.

**Step 2 — Route on exit code**

| Exit | Status | Action |
|------|--------|--------|
| 0 | converged / nothing_to_do | Done. Report to user. |
| 1 | error | Report error. Stop. |
| 2 | fp_dispatched | MCP dispatch (Step 3) |
| 3 | fh_gate_pending | F_H evaluation (proxy or wait) |
| 4 | fd_gap | F_D checks still failing after F_P resolved — Step 4 |
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

**Step 4 — fd_gap recovery (exit code 4 only)**

F_D checks are still failing after F_P was previously resolved. The engine stopped to
avoid looping indefinitely. The skill re-dispatches the F_P actor with updated context
(the engine rebuilds the manifest with current F_D failure output):

```
Run Step 1 with --edge {output["edge"]}
```

If exit is again 4 on the same edge after a second dispatch, stop and surface F_D
failures to the user. This prevents infinite re-dispatch on broken F_D evaluators.

## F_H Gate (exit code 3)

Surface the gate output to the user verbatim.

**If `--human-proxy` is NOT active** (`human_required and not proxy_mode`): Wait for human decision.
- On approval: emit `review_approved` event via F_D logger, then go to Step 1:
  ```bash
  PYTHONPATH=.genesis python -m genesis emit-event \
    --type review_approved \
    --data '{"feature": "{F}", "edge": "{E}", "actor": "human"}'
  ```
- On rejection: stop. Report to user.

**If `--human-proxy` IS active**: Do NOT pause. Execute proxy evaluation protocol:
1. Load the candidate artifact and the F_H criteria for this edge
2. For each F_H criterion, evaluate with explicit evidence:
   - `Criterion`: name of the check
   - `Evidence`: specific text or observation from the artifact
   - `Satisfied`: yes/no with reasoning
3. Decision: `approved` if every required criterion passes; `rejected` if any fail
4. Write proxy-log to `.ai-workspace/reviews/proxy-log/{ISO}_{feature}_{edge}.md` BEFORE emitting any event:
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
5. On proxy approval: emit event, then go to Step 1:
   ```bash
   PYTHONPATH=.genesis python -m genesis emit-event \
     --type review_approved \
     --data '{"feature": "{F}", "edge": "{E}", "actor": "human-proxy", "proxy_log": "{path}"}'
   ```
6. On proxy rejection: emit `review_rejected` with `actor: "human-proxy"`. Set feature
   to `iterating`. Do not retry this edge in the same session. Continue loop on other features.

## Human Proxy Mode (`--human-proxy`)

**Requires `--auto`.** Used alone is an error: `--human-proxy requires --auto`.

When active, displays `[proxy mode active]` banner at session start.

The flag is a **per-invocation** option — never persisted to workspace state,
never activated by config, env var, or inference. Must be supplied explicitly every invocation.

If incomplete proxy-log entries exist from a previous session (interrupted before
the proxy log was written), they are reported at session start for morning review.

Proxy decisions are provisional. `gen-status` surfaces them for morning review.

## Progressive Disclosure

On first run (empty events.jsonl or missing `.ai-workspace`), show only the
essential ≤5 questions. This is the 5-question initialisation flow:

1. Project name
2. Project kind (library / service / CLI / data pipeline / other)
3. Primary language
4. Test runner
5. Initial intent (what are you building?)

Advanced configuration (graph topology, profiles, context hierarchy) is deferred
until after the first iteration completes.
