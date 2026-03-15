# /gen-consensus-recover — Select Recovery Path After CONSENSUS Failure

<!-- Implements: REQ-F-CONS-008, REQ-F-CONSENSUS-001 -->
<!-- Reference: ADR-S-025 §Phase 5 (Recovery), ADR-S-031 (saga compensation pattern) -->
<!-- Design: imp_claude/design/CONSENSUS_DESIGN.md §Recovery Paths -->

Select and execute a recovery path after a `consensus_failed` event. This command
is the **proposer's response** to saga failure — a deliberate human decision
(`F_H`) about how to proceed when consensus was not reached.

This is a **thin emitter** — it validates the situation, presents options, then
emits `recovery_path_selected` and the appropriate follow-up event.

## Usage

```
/gen-consensus-recover --review-id <id> --path <re_open|narrow_scope|abandon> [--rationale "<text>"] [--review-closes-in <seconds>]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--review-id` | required | The failed review session ID |
| `--path` | required | Recovery path: `re_open`, `narrow_scope`, or `abandon` |
| `--rationale` | recommended | Explanation for the path chosen |
| `--review-closes-in` | `86400` | For `re_open`: new window duration in seconds (default: 24h) |

## Recovery paths

| Path | When to use | Outcome |
|------|------------|---------|
| `re_open` | Participation was low or relays need more time | New review window, same artifact and roster |
| `narrow_scope` | Contested section can be extracted — rest is agreed | Fold-back to intent edge; artifact scoped down; new review cycle |
| `abandon` | Proposal is not viable in current form | Feature closed as `consensus_failed`; no new review |

**Availability by failure reason** (from `consensus_failed` event `available_paths`):

| `failure_reason` | Available paths |
|------------------|----------------|
| `quorum_not_reached` | `re_open`, `narrow_scope`, `abandon` |
| `tie` | `re_open`, `narrow_scope`, `abandon` |
| `participation_floor_not_met` | `re_open`, `abandon` |
| `gating_comments_undispositioned` | `disposition_comments` — use `/gen-dispose` first |
| `window_closed_insufficient_votes` | `re_open`, `abandon` |

## Instructions

### Step 1: Validate inputs

1. Confirm `--review-id` and `--path` are provided
2. Confirm `--path` is one of `re_open`, `narrow_scope`, `abandon`
3. Read `.ai-workspace/events/events.jsonl`:
   - Verify a `consensus_failed` event exists for `review_id` — recovery only valid after failure
   - Verify no `recovery_path_selected` already exists for this `review_id` — prevent double-recovery
   - Extract `available_paths` from the `consensus_failed` event
   - Verify `--path` is in `available_paths`
4. If `failure_reason` is `gating_comments_undispositioned`: exit with guidance to use `/gen-dispose`

### Step 2: Emit `recovery_path_selected`

Append to `.ai-workspace/events/events.jsonl`:

```json
{
  "event_type": "recovery_path_selected",
  "review_id": "{review_id}",
  "timestamp": "{ISO 8601 UTC}",
  "project": "{project_name}",
  "actor": "local-user",
  "data": {
    "failed_review_id": "{review_id}",
    "path": "{re_open|narrow_scope|abandon}",
    "rationale": "{rationale text or empty string}"
  }
}
```

### Step 3: Execute path-specific follow-on

#### `re_open`

Open a new review session for the same artifact:

1. Extract original `consensus_requested` event to get `artifact`, `roster`, `quorum`, `abstention_model`, `min_participation_ratio`, `min_duration_seconds`
2. Compute `new_review_closes_at` = now + `--review-closes-in` seconds
3. Generate new `review_id`: `REVIEW-{slug}-{n+1}` (increment count of existing `consensus_requested` events)
4. Append `consensus_requested` event with new `review_id` and updated `review_closes_at`
5. Link to prior session in `data.prior_review_id`

```json
{
  "event_type": "consensus_requested",
  "review_id": "{new_review_id}",
  "timestamp": "{ISO 8601 UTC}",
  "project": "{project_name}",
  "actor": "local-user",
  "data": {
    "artifact": "{artifact_path}",
    "asset_version": "v1",
    "prior_review_id": "{failed_review_id}",
    "roster": [{...}],
    "quorum": "{quorum_threshold}",
    "abstention_model": "neutral",
    "min_participation_ratio": 0.5,
    "published_at": "{ISO 8601 UTC}",
    "review_closes_at": "{new_review_closes_at}",
    "min_duration_seconds": 0
  }
}
```

#### `narrow_scope`

Fold back to the intent edge to reduce artifact scope:

1. Extract `artifact` from original `consensus_requested`
2. Emit `recovery_path_selected` (already done in Step 2)
3. Present to human: which section(s) are contested? The proposer must manually edit the artifact and re-open a new review.

```
To proceed with narrow_scope:
  1. Edit the artifact: {artifact_path}
     Remove or defer the contested sections identified in the review thread.
  2. Publish the revised artifact:
     /gen-consensus-open --artifact {artifact_path} --roster {roster} --quorum {quorum}
  3. The new review begins with the reduced scope.
```

**Note**: `narrow_scope` requires human judgment — which portions to remove is an `F_H` decision. This command records the intent; the proposer executes the edit.

#### `abandon`

Close the feature as irresolvable in current form:

1. Emit `recovery_path_selected` (already done in Step 2)
2. No further events. The feature vector status will reflect `consensus_failed`.
3. The `consensus_failed` + `recovery_path_selected(abandon)` pair is the terminal state.

### Step 4: Report

```
Recovery path selected: {review_id}
  Path:      {re_open | narrow_scope | abandon}
  Rationale: {rationale or "(none)"}

{If re_open:}
  New review session: {new_review_id}
  Artifact:   {artifact_path}
  Roster:     {roster_ids joined by ", "}
  Window:     {new_review_closes_at} ({hours}h from now)

  Relays will react when triggered. To check status:
    /gen-consensus-status --review-id {new_review_id}

{If narrow_scope:}
  Next steps:
    1. Edit {artifact_path} to remove contested sections
    2. Re-open: /gen-consensus-open --artifact {artifact_path} --roster ...

{If abandon:}
  Feature {artifact_path} closed as consensus_failed.
  No further review will be opened for this artifact version.
  To resume: create a new artifact version and open a new review.

{Stuck delta warning — if re_open count >= 3 for same artifact:}
  ⚠ Warning: {n} re_open cycles for this artifact without convergence.
  Homeostasis monitor will detect this stuck delta pattern.
  Consider narrow_scope or abandon — re-opening without addressing root causes
  is unlikely to reach a different outcome.
```

## Invariants (ADR-S-031 §Compensation Pattern)

Recovery is **compensating action in a saga** — not reversal. The `consensus_failed`
event is immutable. Recovery opens a new saga branch rather than undoing the old one.

| Invariant | What it means |
|-----------|---------------|
| Recovery requires `consensus_failed` | Prevents recovery on open or converged sessions |
| `recovery_path_selected` is immutable | Cannot change path after selection |
| `re_open` creates a new session | The failed session remains closed; a sibling session begins |
| `abandon` is terminal | No further review cycle is possible without a new artifact version |
| `narrow_scope` requires human edit | This command records intent; the proposer acts |

## Examples

```bash
# Re-open with extended window (72h) after low participation
/gen-consensus-recover \
  --review-id REVIEW-ADR-S-027-1 \
  --path re_open \
  --review-closes-in 259200 \
  --rationale "Low participation — extending window and notifying absent reviewers directly."

# Narrow scope — contested section to be extracted to separate ADR
/gen-consensus-recover \
  --review-id REVIEW-ADR-S-027-1 \
  --path narrow_scope \
  --rationale "Veto audit trail section is contested. Extracting to ADR-S-033. Core veto semantics are agreed."

# Abandon — proposal not viable
/gen-consensus-recover \
  --review-id REVIEW-ADR-S-027-1 \
  --path abandon \
  --rationale "Fundamental disagreement on veto scope. Deferring until ADR-S-028 (capability boundaries) is ratified."
```
