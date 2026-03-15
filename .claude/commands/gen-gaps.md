# /gen-gaps - Traceability Validation

Run formal traceability validation across 3 layers: REQ tag coverage, test gap analysis, and telemetry gap analysis. Reports gaps with severity and recommended actions.

<!-- Implements: REQ-TOOL-005 -->
<!-- Implements: REQ-TOOL-009 -->
<!-- Implements: REQ-EVOL-003 -->
<!-- Implements: REQ-TEST-001 -->
<!-- Implements: REQ-TEST-004 -->

## Usage

```
/gen-gaps [--layer 1|2|3|all] [--scope code|tests|telemetry|all] [--feature "REQ-F-*"]
```

| Option | Description |
|--------|-------------|
| `--layer` | Which traceability layer to run (default: all) |
| `--scope` | Focus analysis on specific asset type (default: all) |
| `--feature` | Limit analysis to a specific feature vector |

## Layers

| Layer | What it checks | Required at |
|-------|---------------|-------------|
| **1: REQ Tag Coverage** | Code has `Implements:` tags, tests have `Validates:` tags | design→code, code↔tests |
| **2: Test Gap Analysis** | Every REQ key in spec has at least one test | code↔tests, code→cicd |
| **3: Telemetry Gap Analysis** | Every REQ key in code has telemetry tagging | code→cicd, telemetry→intent |

## Instructions

### Step 1: Build REQ Key Inventory (Source of Truth)

Collect all REQ keys from the specification:

```bash
# Primary source: requirements specification
grep -n "REQ-" specification/requirements.md specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md 2>/dev/null

# Secondary source: feature vector files
grep -rn "feature:" .ai-workspace/features/active/ 2>/dev/null
```

Build the **spec inventory**: the complete set of defined REQ keys.

### Step 2: Layer 1 — REQ Tag Coverage

Scan code and test files for REQ key tags:

```bash
# Code tags
grep -rn "Implements: REQ-" src/ lib/ app/ 2>/dev/null

# Test tags
grep -rn "Validates: REQ-" tests/ test/ spec/ 2>/dev/null
```

For each file, check:
- **Code files**: Does every production code file have at least one `Implements: REQ-*` tag?
- **Test files**: Does every test file have at least one `Validates: REQ-*` tag?
- **Format**: Do all tags follow `REQ-{TYPE}-{DOMAIN}-{SEQ}` format?
- **Validity**: Do all referenced REQ keys exist in the spec inventory?

Report as evaluator checklist:

```
═══ LAYER 1: REQ TAG COVERAGE ═══

┌────────────────────────────┬───────────────┬────────┬──────────┐
│ Check                      │ Type          │ Result │ Required │
├────────────────────────────┼───────────────┼────────┼──────────┤
│ req_tags_in_code           │ deterministic │ {P/F}  │ yes      │
│ req_tags_in_tests          │ deterministic │ {P/F}  │ yes      │
│ req_tags_valid_format      │ deterministic │ {P/F}  │ yes      │
│ req_keys_exist_in_spec     │ agent         │ {P/F}  │ yes      │
└────────────────────────────┴───────────────┴────────┴──────────┘

UNTAGGED CODE FILES:
  - src/utils/helpers.py (no Implements: REQ-* tag)

UNTAGGED TEST FILES:
  - tests/test_utils.py (no Validates: REQ-* tag)

ORPHAN REQ KEYS (referenced but not in spec):
  - REQ-F-LEGACY-001 (in src/old_module.py:12)
═══════════════════════════
```

### Step 3: Layer 2 — Test Gap Analysis

Cross-reference spec inventory against test tags:

For each REQ key in the spec:
1. Search tests for `Validates: {REQ_KEY}`
2. If found: covered. Record which test files cover it.
3. If not found: **TEST GAP**

Report:

```
═══ LAYER 2: TEST GAP ANALYSIS ═══

┌────────────────────────────┬───────────────┬────────┬──────────┐
│ Check                      │ Type          │ Result │ Required │
├────────────────────────────┼───────────────┼────────┼──────────┤
│ all_req_keys_have_tests    │ agent         │ {P/F}  │ yes      │
│ test_to_req_ratio          │ agent         │ {P/F}  │ no       │
└────────────────────────────┴───────────────┴────────┴──────────┘

COVERAGE MAP:
| REQ Key            | Tests | Files                          |
|--------------------|-------|--------------------------------|
| REQ-F-AUTH-001     | 3     | test_auth.py, test_login.py    |
| REQ-F-AUTH-002     | 0     | ** TEST GAP **                 |
| REQ-NFR-PERF-001   | 1     | test_performance.py            |

Summary:
  Total REQ keys:       15
  With tests:           12 (80%)
  WITHOUT tests:         3 (20%) ← TEST GAPS
  Avg tests/REQ:        2.1

TEST GAPS (no test validates this REQ key):
  - REQ-F-AUTH-002: "User password reset"
  - REQ-NFR-SEC-003: "Rate limiting on auth endpoints"
  - REQ-DATA-AUDIT-001: "Audit log retention"
═══════════════════════════
```

### Step 4: Layer 3 — Telemetry Gap Analysis

Cross-reference code REQ tags against telemetry:

For each REQ key in code (`Implements: REQ-*`):
1. Search for telemetry references: `req="REQ-*"` or `req='REQ-*'`
2. Also check for logger calls, metrics, and observability tags
3. If found: monitored. Record where.
4. If not found: **TELEMETRY GAP**

```bash
# Telemetry tags
grep -rn 'req="REQ-\|req=.REQ-' src/ lib/ app/ 2>/dev/null
```

Report:

```
═══ LAYER 3: TELEMETRY GAP ANALYSIS ═══

┌────────────────────────────────┬───────────────┬────────┬──────────┐
│ Check                          │ Type          │ Result │ Required │
├────────────────────────────────┼───────────────┼────────┼──────────┤
│ code_req_keys_have_telemetry   │ agent         │ {P/F}  │ no*      │
│ telemetry_tag_format           │ deterministic │ {P/F}  │ no*      │
└────────────────────────────────┴───────────────┴────────┴──────────┘
* Required at code→cicd and telemetry→intent edges

TELEMETRY MAP:
| REQ Key            | In Code | In Telemetry | Status        |
|--------------------|---------|--------------|---------------|
| REQ-F-AUTH-001     | Y       | Y            | Monitored     |
| REQ-F-AUTH-002     | Y       | N            | TELEMETRY GAP |
| REQ-F-DB-001       | Y       | Y            | Monitored     |

Summary:
  REQ keys in code:     12
  With telemetry:        8 (67%)
  WITHOUT telemetry:     4 (33%) ← TELEMETRY GAPS

TELEMETRY GAPS (feature running without observability):
  - REQ-F-AUTH-002: No req= tag in logging/metrics
  - REQ-NFR-PERF-001: No req= tag in logging/metrics
═══════════════════════════
```

### Step 5: Consolidated Report

```
═══ TRACEABILITY VALIDATION REPORT ═══
Project:    {project_name}
Date:       {timestamp}
Feature:    {feature or "all"}

LAYER RESULTS:
  Layer 1 (REQ Tags):    {PASS|FAIL} — {n} of {m} checks pass
  Layer 2 (Test Gaps):   {PASS|FAIL} — {n} of {m} checks pass
  Layer 3 (Telemetry):   {PASS|FAIL} — {n} of {m} checks pass

FULL COVERAGE MAP:
| REQ Key            | Design | Code | Tests | Telemetry | Status    |
|--------------------|--------|------|-------|-----------|-----------|
| REQ-F-AUTH-001     | Y      | Y    | Y     | Y         | COMPLETE  |
| REQ-F-AUTH-002     | Y      | Y    | N     | N         | GAPS      |
| REQ-NFR-PERF-001   | Y      | N    | N     | N         | GAPS      |

SUMMARY:
  Total REQ keys:       {n}
  Full coverage:        {n} ({pct}%)
  Partial coverage:     {n} ({pct}%)
  No coverage:          {n} ({pct}%)

CRITICAL GAPS (ordered by severity):
  1. REQ-NFR-PERF-001: No code, no tests, no telemetry
  2. REQ-F-AUTH-002: No tests, no telemetry
  3. REQ-F-AUTH-001: Missing telemetry only

RECOMMENDED NEXT ACTIONS:
  1. /gen-iterate --edge "design→code" --feature "REQ-F-PERF-001"
  2. /gen-iterate --edge "code↔unit_tests" --feature "REQ-F-AUTH-002"
  3. Add telemetry tagging: req="REQ-F-AUTH-001" to auth logging
═══════════════════════════
```

### Step 6: Emit Events

**6a. Emit `gaps_validated` event**:

```json
{"event_type": "gaps_validated", "timestamp": "{ISO 8601}", "project": "{project name from project_constraints.yml}", "data": {"layers_run": [1, 2, 3], "feature": "{feature or 'all'}", "total_req_keys": {n}, "full_coverage": {n}, "partial_coverage": {n}, "no_coverage": {n}, "test_gaps": {n}, "telemetry_gaps": {n}, "layer_results": {"layer_1": "pass|fail", "layer_2": "pass|fail", "layer_3": "pass|fail"}}}
```

**6b. Emit `intent_raised` events for each gap cluster** (consciousness loop at gap observer):

Gap analysis IS homeostasis during development. Every uncovered REQ key is a delta between the spec (what should be tested/monitored) and reality (what actually is). For each cluster of related gaps, emit:

```json
{"event_type": "intent_raised", "timestamp": "{ISO 8601}", "project": "{project name}", "data": {"intent_id": "INT-{SEQ}", "trigger": "/gen-gaps layer {n} found {count} uncovered REQ keys", "delta": "{count} REQ keys without {test|telemetry} coverage", "signal_source": "gap", "vector_type": "feature", "affected_req_keys": ["REQ-*", "..."], "prior_intents": [], "edge_context": "gap_analysis", "severity": "high"}}
```

Clustering rules:
- Group gaps by **domain** (e.g., all `REQ-F-AUTH-*` gaps → one intent)
- Test gaps (Layer 2) are **High** priority — features running without verification
- Telemetry gaps (Layer 3) are **Medium** priority — features running without observability
- REQ tag gaps (Layer 1) are **High** priority — code without traceability

Present the generated intents to the human. They decide which to pursue.

**6c. Emit `feature_proposal` events for each intent cluster** (consciousness loop Stage 2 — Affect Triage):

For each `intent_raised` cluster emitted in 6b, immediately emit a companion `feature_proposal` event. This is the Affect Triage output: the system classifies severity, drafts a candidate feature vector, and places it in the review queue.

```json
{
  "event_type": "feature_proposal",
  "timestamp": "{ISO 8601}",
  "project": "{project name}",
  "data": {
    "proposal_id": "PROP-{SEQ}",
    "intent_id": "INT-{SEQ}",
    "title": "{short description of the proposed feature}",
    "description": "{what the feature would implement — 2-3 sentences}",
    "affected_req_keys": ["REQ-*", "..."],
    "severity": "high|medium|low",
    "vector_type": "feature",
    "suggested_profile": "standard|hotfix|spike",
    "status": "draft",
    "source": "gap_analysis",
    "review_path": ".ai-workspace/reviews/pending/PROP-{SEQ}.yml"
  }
}
```

For each proposal, write a structured YAML file to `.ai-workspace/reviews/pending/PROP-{SEQ}.yml`:

```yaml
proposal_id: "PROP-{SEQ}"
intent_id: "INT-{SEQ}"
status: draft
severity: high|medium|low
created: "{ISO 8601}"
source: gap_analysis

title: "{short description}"
description: |
  {what the feature would implement}

affected_req_keys:
  - REQ-*

suggested_vector:
  feature: "REQ-F-{DOMAIN}-{NEXT_SEQ}"
  title: "{title}"
  vector_type: feature
  profile: standard|hotfix|spike
  requirements: [REQ-*, ...]

review_instructions: |
  Approve: /gen-review-proposal --approve PROP-{SEQ}
  Dismiss: /gen-review-proposal --dismiss PROP-{SEQ} --reason "{reason}"
```

The review queue is surfaced by `/gen-status` (REQ-UX-006: escalation awareness).
`/gen-review-proposal` is the Stage 3 human gate that processes this queue.

## Examples

```bash
# Run full traceability validation
/gen-gaps

# Check only test coverage gaps
/gen-gaps --layer 2

# Check telemetry gaps only
/gen-gaps --layer 3

# Check gaps for a specific feature
/gen-gaps --feature "REQ-F-AUTH-001"

# Check only code tag coverage
/gen-gaps --layer 1 --scope code
```
