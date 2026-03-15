# /gen-vote — Cast a Vote in a CONSENSUS Review Session

<!-- Implements: REQ-F-CONS-005, REQ-F-CONSENSUS-001, REQ-EVAL-003 -->
<!-- Reference: ADR-S-025 §Phase 3 (Voting), ADR-S-031 (F_H relay) -->
<!-- Design: imp_claude/design/CONSENSUS_DESIGN.md §Component 5 -->

Cast a vote (`approve`, `reject`, or `abstain`) in an open CONSENSUS review session.
Emits a `vote_cast` event and reports the current tally. Quorum evaluation is the
quorum observer's responsibility — this command does not run the quorum check.

## Usage

```
/gen-vote --review-id <id> --verdict <approve|reject|abstain> [--rationale "<text>"] [--gating]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--review-id` | required | The review session ID (e.g. `REVIEW-ADR-S-027-1`) |
| `--verdict` | required | `approve`, `reject`, or `abstain` |
| `--rationale` | optional | Explanation for your vote (strongly recommended) |
| `--gating` | false | Mark this vote as containing a gating comment (blocks consensus until dispositioned) |
| `--participant` | auto | Override participant ID (defaults to current agent/user) |

## Instructions

### Step 1: Validate inputs

1. Confirm `--review-id` is provided
2. Confirm `--verdict` is one of `approve`, `reject`, `abstain`
3. Read `.ai-workspace/events/events.jsonl` — verify a `consensus_requested` event exists for this `review_id`
4. Verify no prior `consensus_reached` or `consensus_failed` event exists for this `review_id` (session must be open)
5. Note: duplicate votes are now allowed (most-recent-per-relay semantics). A participant may revise their vote as the artifact evolves. The prior vote is superseded — do NOT reject revisions.

### Step 2: Identify participant

Determine the participant ID:
- If `--participant` is specified, use it
- Otherwise, use the current agent role name (e.g. `gen-dev-observer`, `gen-cicd-observer`, `gen-ops-observer`)
- For human votes: use `local-user`

Verify the participant is in the roster from the `consensus_requested` event.
If not in roster, emit a warning: `{participant} is not in the review roster — vote recorded but will not count toward quorum`

### Step 3: Emit `vote_cast` event

Append to `.ai-workspace/events/events.jsonl`:

```json
{
  "event_type": "vote_cast",
  "review_id": "{review_id}",
  "timestamp": "{ISO 8601}",
  "project": "{project_name}",
  "actor": "{participant_id}",
  "data": {
    "participant": "{participant_id}",
    "asset_version": "{asset_version from consensus_requested event, default v1}",
    "verdict": "{approve|reject|abstain}",
    "rationale": "{rationale text or empty string}"
  }
}
```

If `--gating` is set, also emit a `comment_received` event with `gating: true` so the rationale appears in the comment thread:

```json
{
  "event_type": "comment_received",
  "review_id": "{review_id}",
  "timestamp": "{ISO 8601}",
  "project": "{project_name}",
  "actor": "{participant_id}",
  "data": {
    "participant": "{participant_id}",
    "content": "{rationale}",
    "gating": true,
    "disposition": null
  }
}
```

### Step 4: Read and report current tally

Read the event log to produce a current tally for display. This is a read-only projection —
no quorum check is run. The quorum observer's responsibility is to detect convergence.

```bash
python -c "
from imp_claude.code.genesis.consensus_engine import project_review_state, _parse_ts
import json, pathlib

review_id = '{review_id}'
events = [json.loads(l) for l in pathlib.Path('.ai-workspace/events/events.jsonl').read_text().splitlines() if l.strip()]
req_ev = next((e for e in events if e.get('event_type') == 'consensus_requested' and e.get('review_id') == review_id), None)
if not req_ev:
    print('no_session')
    exit()
data = req_ev.get('data', req_ev)
roster = data.get('roster', [])
roster_ids = [r['id'] if isinstance(r, dict) else r for r in roster]
close_time = _parse_ts(data.get('review_closes_at', ''))
votes, comments = project_review_state(events, review_id, close_time)
approves = sum(1 for v in votes if v.verdict.value == 'approve')
rejects = sum(1 for v in votes if v.verdict.value == 'reject')
abstains = sum(1 for v in votes if v.verdict.value == 'abstain')
voted_ids = {v.participant for v in votes}
pending = [r for r in roster_ids if r not in voted_ids]
print(f'approve={approves} reject={rejects} abstain={abstains} pending={len(pending)}')
"
```

### Step 5: Report

```
Vote cast: {review_id}
  Participant: {participant_id}
  Verdict:     {approve ✓ | reject ✗ | abstain ~}
  Rationale:   {rationale or "(none)"}
  Version:     {asset_version}

Current tally ({responded}/{roster_size} responded):
  ✓ approve:  {n}
  ✗ reject:   {n}
  ~ abstain:  {n}
  · pending:  {pending_count} — {pending_ids}

Quorum evaluation is handled by the quorum observer.
```

**Important**: this command does not emit `consensus_reached` or `consensus_failed`.
Those are emitted by the quorum observer when it reacts to the `vote_cast` event.

## Examples

```bash
# Approve an ADR as the dev observer
/gen-vote \
  --review-id REVIEW-ADR-S-027-1 \
  --verdict approve \
  --rationale "Veto semantics are well-specified and consistent with ADR-S-025 quorum algebra."

# Reject with a gating concern
/gen-vote \
  --review-id REVIEW-ADR-S-027-1 \
  --verdict reject \
  --rationale "Missing: rollback path if veto is exercised mid-sequence." \
  --gating

# Abstain (no opinion on this domain)
/gen-vote \
  --review-id REVIEW-ADR-S-027-1 \
  --verdict abstain \
  --rationale "CI/CD-neutral change — no opinion from this observer."
```
