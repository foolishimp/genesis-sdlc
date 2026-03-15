# /gen-review-proposal - Human Evaluator Review Point (Stage 3)

Review draft feature proposals from the Affect Triage queue. This is the consciousness loop Stage 3 human gate (ADR-011, ADR-S-008): proposals arrive from gap analysis or sensory signals; the human approves or dismisses them; approved proposals inflate workspace trajectory.

<!-- Implements: REQ-F-EVOL-001 (Spec Evolution Pipeline), REQ-UX-006 (Human Gate Awareness), REQ-EVOL-003 (Feature Proposal Queue), REQ-EVOL-005 (Draft Queue Visibility) -->
<!-- Reference: ADR-011 (Consciousness Loop), ADR-S-008 (Sensory Triage Intent Pipeline), ADR-S-010 (Event-Sourced Spec Evolution) -->

## Usage

```
/gen-review-proposal [--list] [--approve PROP-NNN] [--dismiss PROP-NNN --reason "..."] [--show PROP-NNN]
```

| Option | Description |
|--------|-------------|
| `--list` | List all pending proposals (default if no option given) |
| `--show PROP-NNN` | Show full detail for a specific proposal |
| `--approve PROP-NNN` | Approve a proposal — inflates workspace trajectory and emits spec_modified |
| `--dismiss PROP-NNN --reason "..."` | Dismiss a proposal with a reason — archives it |

## Instructions

### Step 0: Load Pending Proposals

Read all YAML files from `.ai-workspace/reviews/pending/PROP-*.yml`. Each file is a draft feature proposal emitted by Stage 2 (Affect Triage in `/gen-gaps` or sensory monitors).

If no `--option` is given, default to `--list`.

### Step 1: List (--list)

Display a summary table of all pending proposals:

```
Pending Feature Proposals
=========================
Count: {n} proposals awaiting review

┌───────────┬──────────────────────────────────────────┬──────────┬────────┬───────────┐
│ ID        │ Title                                    │ Severity │ Source │ Created   │
├───────────┼──────────────────────────────────────────┼──────────┼────────┼───────────┤
│ PROP-001  │ Add tests for REQ-F-AUTH-002             │ high     │ gaps   │ 2026-03-06│
│ PROP-002  │ Telemetry for REQ-F-DB-001               │ medium   │ gaps   │ 2026-03-06│
└───────────┴──────────────────────────────────────────┴──────────┴────────┴───────────┘

Use /gen-review-proposal --show PROP-NNN to see full detail.
Use /gen-review-proposal --approve PROP-NNN or --dismiss PROP-NNN --reason "..." to act.
```

If no proposals pending: "No pending proposals. The review queue is empty."

### Step 2: Show (--show PROP-NNN)

Display the full proposal detail:

```
Proposal: PROP-001
==================
Status:   draft
Severity: high
Source:   gap_analysis (Layer 2 — test coverage gap)
Created:  {timestamp}
Intent:   INT-{SEQ}

Title: Add tests for REQ-F-AUTH-002 "User password reset"

Description:
  {description from proposal YAML}

Affected REQ Keys:
  - REQ-F-AUTH-002 (no tests)
  - REQ-F-AUTH-003 (no tests)

Suggested Vector:
  Feature: REQ-F-AUTH-001 (extend existing)
  Profile: standard
  Edge:    code↔unit_tests

Actions:
  Approve:  /gen-review-proposal --approve PROP-001
  Dismiss:  /gen-review-proposal --dismiss PROP-001 --reason "covered by REQ-F-AUTH-004"
```

### Step 3: Approve (--approve PROP-NNN)

**Stage 3 approval path** — human confirms the proposal should become a tracked feature vector.

#### Step 3a: Validate proposal

1. Load `.ai-workspace/reviews/pending/PROP-{NNN}.yml`
2. Verify `status: draft` (not already actioned)
3. Verify `suggested_vector.feature` does not already exist in `.ai-workspace/features/active/`

#### Step 3b: Inflate workspace trajectory

Create a new feature vector file at `.ai-workspace/features/active/{suggested_feature_id}.yml`:

```yaml
feature: "{suggested_vector.feature}"
title: "{suggested_vector.title}"
intent: "{proposal.intent_id}"
vector_type: "{suggested_vector.vector_type}"
profile: "{suggested_vector.profile}"
status: pending
priority: "{proposal.severity}"
created: "{ISO 8601}"
updated: "{ISO 8601}"
source: feature_proposal
proposal_id: "{proposal.proposal_id}"

requirements: {suggested_vector.requirements}

trajectory:
  requirements:
    status: pending
  design:
    status: pending
  code:
    status: pending
  unit_tests:
    status: pending
```

#### Step 3c: Append to FEATURE_VECTORS.md

Append a summary of the new feature vector to `specification/features/FEATURE_VECTORS.md` (or the corresponding spec file) to maintain the formal specification anchor:

```markdown
### {suggested_vector.feature}: {suggested_vector.title}
- **Intent**: {proposal.intent_id}
- **Requirements**: {req_keys}
```

#### Step 3d: Update ACTIVE_TASKS.md

Append a new task entry to `.ai-workspace/tasks/active/ACTIVE_TASKS.md`:

```markdown
## New: {feature_id} — {title}

**Status**: Pending
**Source**: PROP-{NNN} (approved {date})
**Priority**: {severity}

{description}

**Requirements**: {req_keys}
**Start with**: /gen-iterate --edge "intent→requirements" --feature "{feature_id}"
```

#### Step 3e: Emit events

Emit `feature_proposal` status update and `spec_modified` events:

```json
{"event_type": "feature_proposal", "timestamp": "{ISO 8601}", "project": "{project}", "data": {"proposal_id": "PROP-{NNN}", "intent_id": "{intent_id}", "status": "approved", "feature_id": "{feature_id}", "approved_by": "human"}}
```

```json
{"event_type": "spec_modified", "timestamp": "{ISO 8601}", "project": "{project}", "data": {"modification_type": "feature_vector_created", "feature_id": "{feature_id}", "source": "PROP-{NNN}", "files_modified": [".ai-workspace/features/active/{feature_id}.yml", "specification/features/FEATURE_VECTORS.md", ".ai-workspace/tasks/active/ACTIVE_TASKS.md"]}}
```

#### Step 3f: Archive proposal

Move `.ai-workspace/reviews/pending/PROP-{NNN}.yml` to `.ai-workspace/reviews/approved/PROP-{NNN}.yml`. Update `status: approved`, add `approved_at`, `feature_id`.

#### Step 3g: Report

```
Proposal PROP-{NNN} approved
==============================
Feature vector created: .ai-workspace/features/active/{feature_id}.yml
Tasks updated:          .ai-workspace/tasks/active/ACTIVE_TASKS.md
Events emitted:         feature_proposal (approved), spec_modified

Next step: /gen-start  (will detect new pending feature and route to intent→requirements)
```

### Step 4: Dismiss (--dismiss PROP-NNN --reason "...")

**Stage 3 dismissal path** — human decides the proposal should not be pursued.

1. Load `.ai-workspace/reviews/pending/PROP-{NNN}.yml`
2. Verify `status: draft`
3. Archive: move to `.ai-workspace/reviews/dismissed/PROP-{NNN}.yml`, update `status: dismissed`, add `dismissed_at`, `dismissed_reason`
4. Emit event:
   ```json
   {"event_type": "feature_proposal_dismissed", "timestamp": "{ISO 8601}", "project": "{project}", "data": {"proposal_id": "PROP-{NNN}", "intent_id": "{intent_id}", "reason": "{reason}", "dismissed_by": "human"}}
   ```
5. Report: "Proposal PROP-{NNN} dismissed. Reason recorded. Review queue updated."

### Step 5: Post-Action State Check

After any approve or dismiss action, display the updated queue count:

```
Review queue: {n} proposals remaining
```

If the queue is now empty: "Review queue is empty. Run /gen-start to continue iteration."

## Consciousness Loop Connection

This command is the **Stage 3 human gate** in the consciousness loop (ADR-011):

```
Stage 1 (gen-gaps/sensory): delta detected → intent_raised event
Stage 2 (Affect Triage):    intent classified → feature_proposal event + review queue entry
Stage 3 (this command):     human reviews → approve (spec grows) | dismiss (archived)
```

The `spec_modified` event on approval is the signal that the constraint surface has changed. It triggers:
- `gen-status` to show the new feature in the pending list
- `gen-start` to detect IN_PROGRESS and route to the new feature's first edge
- The homeostasis loop: the system now tracks a new delta and works to close it

Without Stage 3, intents accumulate in `intent_raised` events but never become actionable work. This command converts observability signals into tracked features — closing the abiogenesis loop.

## Examples

```bash
# See all pending proposals
/gen-review-proposal

# Review a specific proposal
/gen-review-proposal --show PROP-001

# Approve — creates feature vector and tasks
/gen-review-proposal --approve PROP-001

# Dismiss — archive with reason
/gen-review-proposal --dismiss PROP-001 --reason "duplicate of REQ-F-AUTH-004"
```
