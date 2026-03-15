# /gen-consensus-open — Open a CONSENSUS Review Session

<!-- Implements: REQ-F-CONS-001, REQ-F-CONSENSUS-001, REQ-EVAL-003 -->
<!-- Reference: ADR-S-025 §Phase 1 (Publication), ADR-S-031 (Observer/Relay/Saga) -->
<!-- Design: imp_claude/design/CONSENSUS_DESIGN.md §Component 1 -->

Open a multi-stakeholder evaluation session on an artifact. This is a **thin emitter** —
it emits `consensus_requested` to the event log and stops. Observer relays react
independently. No orchestration happens here.

## Usage

```
/gen-consensus-open --artifact <path> --roster <agents> [--quorum majority|supermajority|unanimity] [--min-duration <seconds>] [--review-closes-in <seconds>] [--review-id <id>]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--artifact` | required | Path to the artifact under review (relative to project root) |
| `--roster` | required | Comma-separated participant IDs (agents or `human:<id>`) |
| `--quorum` | `majority` | Quorum threshold: `majority`, `supermajority`, or `unanimity` |
| `--min-duration` | `0` | Minimum deliberation window in seconds (lower-bound constraint) |
| `--review-closes-in` | `86400` | Seconds until review window closes (default: 24h) |
| `--review-id` | auto | Override the review session ID |

## Instructions

### Step 1: Validate inputs

1. Confirm `--artifact` file exists at the given path — exit with error if missing
2. Parse `--roster` into a list of participant entries:
   - Known agent IDs (`gen-dev-observer`, `gen-cicd-observer`, `gen-ops-observer`) → `{id, type: agent}`
   - `human:<name>` prefix → `{id: <name>, type: human}`
   - Any other value → `{id: value, type: human}` with a warning
3. Validate each entry has non-empty `id` — reject empty roster entries
4. Confirm roster is non-empty — exit if empty

### Step 2: Generate session identifiers

1. Generate `review_id` if not provided:
   - Derive slug from artifact path: last path component without extension, lowercase, hyphens
   - Count existing `consensus_requested` events in `.ai-workspace/events/events.jsonl` to ensure uniqueness: `REVIEW-{slug}-{n+1}`
2. Set `published_at` = now (ISO 8601 UTC)
3. Set `review_closes_at` = now + `--review-closes-in` seconds
4. Validate: `review_closes_at >= published_at + min_duration_seconds`
   - If violated: exit with `configuration_invalid — review_closes_at must be >= published_at + min_duration`

### Step 3: Emit `consensus_requested`

Append one line to `.ai-workspace/events/events.jsonl`:

```json
{
  "event_type": "consensus_requested",
  "review_id": "{review_id}",
  "timestamp": "{published_at}",
  "project": "{project_name}",
  "actor": "local-user",
  "data": {
    "artifact": "{artifact_path}",
    "asset_version": "v1",
    "roster": [
      {"id": "{participant_id}", "type": "agent|human"}
    ],
    "quorum": "majority|supermajority|unanimity",
    "abstention_model": "neutral",
    "min_participation_ratio": 0.5,
    "published_at": "{ISO 8601}",
    "review_closes_at": "{ISO 8601}",
    "min_duration_seconds": 0
  }
}
```

**Stop here.** Do not invoke agents. Do not call relay agents. Do not run a quorum check.
Do not monitor for votes. This command's job is complete after the event is written.

The saga self-choreographs:
- Observer relays subscribed to `consensus_requested` will react, check the circuit-breaker,
  evaluate the artifact, and emit `vote_cast`
- The quorum observer subscribed to `vote_cast` will evaluate quorum and emit the terminal event

### Step 4: Report

```
Review {review_id} opened
  Artifact:       {artifact_path}
  Version:        v1
  Roster ({n}):  {participant_ids joined by ", "}
  Quorum:         {quorum_threshold}
  Window closes:  {review_closes_at} ({hours}h from now)
  Min duration:   {min_duration_seconds}s

Relays will react when triggered. To check current tally:
  /gen-consensus-status --review-id {review_id}

To cast a vote (human participants):
  /gen-vote --review-id {review_id} --verdict approve|reject|abstain

To trigger agent relays manually (if not running as hooks):
  Invoke gen-dev-observer, gen-cicd-observer, gen-ops-observer with:
    trigger_event: consensus_requested
    review_id: {review_id}
```

---

## Design rationale (ADR-S-031 §Orchestrator Smell)

The original implementation of this command orchestrated sequential agent invocation and
ran the quorum check inline — an orchestrator pattern. Both were missing invariants:

| Old orchestrated step | Invariant that replaces it |
|----------------------|---------------------------|
| Invoke agents in sequence | Circuit-breaker per relay: relay checks it is in roster and has not yet voted |
| Run quorum check after each vote | Quorum observer subscribes to `vote_cast` and fires automatically |

Once those invariants are expressed locally (in relays and quorum observer), this command
has nothing left to do except emit the opening event.

---

## Examples

```bash
# Open ADR review with three agent relays, majority quorum
/gen-consensus-open \
  --artifact specification/adrs/ADR-S-027-veto-semantics.md \
  --roster gen-dev-observer,gen-cicd-observer,gen-ops-observer \
  --quorum majority

# Open a proposal review with a human participant and minimum deliberation window
/gen-consensus-open \
  --artifact .ai-workspace/reviews/pending/PROP-001.yml \
  --roster gen-dev-observer,human:alice \
  --quorum supermajority \
  --min-duration 3600 \
  --review-closes-in 172800

# Short-window review for CI gate
/gen-consensus-open \
  --artifact imp_claude/design/CONSENSUS_DESIGN.md \
  --roster gen-dev-observer,gen-cicd-observer,gen-ops-observer \
  --quorum majority \
  --review-closes-in 300
```
