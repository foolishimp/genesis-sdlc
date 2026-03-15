# /gen-dispose — Disposition a Gating Comment in a CONSENSUS Review Session

<!-- Implements: REQ-F-CONS-003, REQ-F-CONSENSUS-001 -->
<!-- Reference: ADR-S-025 §Phase 2 (Deliberation), ADR-S-031 (thin emitter) -->
<!-- Design: imp_claude/design/CONSENSUS_DESIGN.md §Component 5 -->

Disposition a gating comment in an open CONSENSUS review session. Dispositioned
gating comments no longer block the `gating_comments_dispositioned` convergence check.
When all gating comments are dispositioned and other checks pass, the quorum observer
can emit `consensus_reached`.

This is a **thin emitter** — it updates `disposition` on the event's logical projection
by appending a `comment_dispositioned` event and, for `scope_change`, also a `spec_modified` event.

## Usage

```
/gen-dispose --review-id <id> --comment-ts <timestamp> --disposition <type> --rationale "<text>" [--participant <id>]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--review-id` | required | The review session ID |
| `--comment-ts` | required | Timestamp of the `comment_received` event being dispositioned |
| `--disposition` | required | One of: `resolved`, `rejected`, `acknowledged`, `scope_change` |
| `--rationale` | required | Non-empty explanation for the disposition decision |
| `--participant` | auto | Who is dispositioning (defaults to `local-user`) |

## Disposition values

| Value | Meaning |
|-------|---------|
| `resolved` | The concern raised in the comment has been addressed in the artifact |
| `rejected` | The concern is not valid or not applicable — proposer explains why |
| `acknowledged` | Concern noted; accepted as a known risk or deferred |
| `scope_change` | Concern is valid but out of scope — triggers `spec_modified` for tracking |

## Instructions

### Step 1: Validate inputs

1. Confirm all required options are provided
2. Confirm `--disposition` is one of `resolved`, `rejected`, `acknowledged`, `scope_change`
3. Confirm `--rationale` is non-empty
4. Read `.ai-workspace/events/events.jsonl`:
   - Verify `consensus_requested` exists for `review_id`
   - Verify no terminal event (`consensus_reached`, `consensus_failed`) for `review_id`
   - Find the `comment_received` event matching `review_id` + `comment-ts`
   - Verify the comment has `gating: true` — late comments need no disposition
   - Verify the comment is not already dispositioned (existing `comment_dispositioned` for same ts)

If any check fails, exit with a clear error message.

### Step 2: Emit `comment_dispositioned`

Append to `.ai-workspace/events/events.jsonl`:

```json
{
  "event_type": "comment_dispositioned",
  "review_id": "{review_id}",
  "timestamp": "{ISO 8601 UTC}",
  "project": "{project_name}",
  "actor": "{participant_id}",
  "data": {
    "comment_timestamp": "{comment-ts}",
    "original_participant": "{participant from comment_received event}",
    "disposition": "{resolved|rejected|acknowledged|scope_change}",
    "rationale": "{rationale text}"
  }
}
```

### Step 3: If `scope_change` — also emit `spec_modified`

If `--disposition scope_change`, append a second event:

```json
{
  "event_type": "spec_modified",
  "review_id": "{review_id}",
  "timestamp": "{ISO 8601 UTC}",
  "project": "{project_name}",
  "actor": "{participant_id}",
  "data": {
    "trigger": "comment_dispositioned scope_change",
    "comment_timestamp": "{comment-ts}",
    "rationale": "{rationale — describes what spec change is needed}"
  }
}
```

This signals that a spec boundary was identified. The `spec_modified` event is consumed
by the spec-watch pipeline (REQ-EVOL-004) and surfaced in `/gen-status` as an unactioned signal.

**Stop here.** Do not evaluate quorum. Quorum re-evaluation happens automatically
when the next `vote_cast` event triggers the quorum observer.

### Step 4: Report

```
Comment dispositioned: {review_id}
  Comment by:    {original_participant} at {comment-ts}
  Disposition:   {resolved|rejected|acknowledged|scope_change}
  Dispositioned by: {participant_id}
  Rationale:     {rationale}

{If scope_change:}
  spec_modified event emitted — appears in /gen-status signals.

Convergence gate:
  Gating comments: {total}
  Dispositioned:   {now_dispositioned}
  Remaining:       {remaining}

{If remaining == 0:}
  All gating comments dispositioned. Quorum observer will re-evaluate on next vote_cast.
  To trigger quorum check now: /gen-vote --review-id {review_id} --verdict abstain --rationale "Re-evaluating after comment disposition"
```

## Projection semantics

The `project_review_state()` function in `consensus_engine.py` resolves dispositions
by joining `comment_received` events with `comment_dispositioned` events on timestamp:

```python
# Pseudocode — disposition lookup
for comment in comment_received_events:
    disp_ev = next(
        (e for e in comment_dispositioned_events
         if e["data"]["comment_timestamp"] == comment.timestamp),
        None
    )
    comment.disposition = disp_ev["data"]["disposition"] if disp_ev else None
```

Events are **immutable** — `comment_received` events are never modified. The disposition
is a separate event that extends the logical record. Replaying events always produces
the same result.

## Examples

```bash
# Resolve a concern — artifact updated to address it
/gen-dispose \
  --review-id REVIEW-ADR-S-027-1 \
  --comment-ts 2026-03-09T14:30:00Z \
  --disposition resolved \
  --rationale "Added §Recovery Paths section to ADR-S-027 addressing partial failure during veto sequence."

# Acknowledge as known risk
/gen-dispose \
  --review-id REVIEW-ADR-S-027-1 \
  --comment-ts 2026-03-09T15:00:00Z \
  --disposition acknowledged \
  --rationale "Partial failure during veto is a known operational risk. Will be addressed in ADR-S-032 (ops runbook)."

# Scope change — triggers spec_modified
/gen-dispose \
  --review-id REVIEW-ADR-S-027-1 \
  --comment-ts 2026-03-09T15:45:00Z \
  --disposition scope_change \
  --rationale "Audit trail for veto decisions is out of scope for this ADR — will be tracked in a separate audit requirements doc."
```
