# /gen-comment — Submit a Comment in a CONSENSUS Review Session

<!-- Implements: REQ-F-CONS-002, REQ-F-CONSENSUS-001 -->
<!-- Reference: ADR-S-025 §Phase 2 (Deliberation), ADR-S-031 (thin emitter) -->
<!-- Design: imp_claude/design/CONSENSUS_DESIGN.md §Component 5 -->

Submit a comment to an open CONSENSUS review session. Comments received during the
review window become **gating comments** — they must be dispositioned before
`consensus_reached` can be emitted. Late comments (after window closes) are recorded
as context only and do not affect the convergence gate.

This is a **thin emitter** — it emits one `comment_received` event and stops.

## Usage

```
/gen-comment --review-id <id> --content "<comment text>" [--participant <id>]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--review-id` | required | The review session ID |
| `--content` | required | The comment text |
| `--participant` | auto | Override participant ID (defaults to `local-user` for human comments) |

## Instructions

### Step 1: Validate inputs

1. Confirm `--review-id` is provided
2. Confirm `--content` is non-empty
3. Read `.ai-workspace/events/events.jsonl` — verify a `consensus_requested` event
   exists for this `review_id`. If none: exit with error.

### Step 2: Determine gating status

1. Extract `review_closes_at` from the `consensus_requested` event data
2. Get current time (ISO 8601 UTC)
3. Check for terminal event (`consensus_reached` or `consensus_failed`) for this `review_id`

**Gating rules**:
- If terminal event exists: `gating: false` — comment is late context only
- If `now <= review_closes_at`: `gating: true` — this is a gating comment
- If `now > review_closes_at`: `gating: false` — submitted after window closed

### Step 3: Emit `comment_received`

Append to `.ai-workspace/events/events.jsonl`:

```json
{
  "event_type": "comment_received",
  "review_id": "{review_id}",
  "timestamp": "{ISO 8601 UTC}",
  "project": "{project_name}",
  "actor": "{participant_id}",
  "data": {
    "participant": "{participant_id}",
    "content": "{comment text}",
    "gating": true,
    "disposition": null
  }
}
```

Set `"gating": true` if the comment is within the review window (see Step 2).
Set `"gating": false` for late comments or comments on closed sessions.

**Stop here.** Do not evaluate quorum. Do not notify relays. Do not modify votes.

### Step 4: Report

```
Comment submitted: {review_id}
  Participant: {participant_id}
  Gating:      {yes — must be dispositioned before consensus | no — late context only}
  Content:     {content preview, first 120 chars}

{If gating: true:}
  This comment blocks convergence until dispositioned.
  To disposition: /gen-dispose --review-id {review_id} --participant {participant_id} --disposition resolved|rejected|acknowledged|scope_change --rationale "<text>"

{If gating: false:}
  Late comment — recorded as context. Does not affect convergence gate.
```

## Gating semantics

A comment is gating when:
- It is submitted during the open review window (`now <= review_closes_at`)
- The session has not yet reached a terminal event

Gating status is **immutable once set**. Replaying the event log always produces the
same gating value for a given `comment_received` event — because gating is determined
by the timestamp on the event, not by current time. This preserves idempotency.

A gating comment with `disposition: null` fails the
`gating_comments_dispositioned` check in `evaluate_quorum()`, blocking `consensus_reached`
until `/gen-dispose` is called to set a disposition.

## Examples

```bash
# Submit a concern during open review
/gen-comment \
  --review-id REVIEW-ADR-S-027-1 \
  --content "The recovery path for partial failure is not specified. What happens if the saga is interrupted mid-sequence?"

# Submit late context after window closes
/gen-comment \
  --review-id REVIEW-ADR-S-027-1 \
  --content "Reference implementation in ADR-S-031 addresses the partial failure case."
```
