# /gen-init — Start New Work in a Genesis Project

<!-- Implements: REQ-UX-003 -->

Initialize a new unit of work: create an INTENT.md (if none exists), define a feature
vector for the new work, and confirm the workspace is ready for `/gen-start`.

## Usage

```
/gen-init [--feature "short description"]
```

| Option | Description |
|--------|-------------|
| (none) | Interactive — ask for intent and feature description |
| `--feature` | Brief description of the new feature (skips interactive prompt) |

## Instructions

### Step 1 — Orient to workspace state

Run the engine to see current state:

```bash
PYTHONPATH=.genesis python -m genesis gaps --workspace .
```

Parse the output. If `converged: true` → previous work is done, ready for new unit.
If gaps exist → show them and ask the user whether to continue existing work (`/gen-start`)
or begin a new parallel feature.

Read `.genesis/genesis.yml` to confirm `package:` and `pythonpath:` are set.
Read `gtl_spec/packages/<slug>.py` to understand the graph (edges, REQ keys, evaluators).

### Step 2 — Capture intent (if INTENT.md does not exist)

If `INTENT.md` is missing at the workspace root, ask:

> What are you trying to build? Describe the problem, the value, and rough scope.
> (This becomes INTENT.md — the anchor document for all downstream work.)

Write `INTENT.md`:

```markdown
# Intent — {project_name}

## Problem
{problem statement}

## Value
{business or user value}

## Scope
{what is in scope / out of scope}
```

If `INTENT.md` already exists, read it and summarise it to the user as context for the new feature.

### Step 3 — Describe the new feature

Ask the user:

> What specifically do you want to build next? Give it a short name (becomes the REQ key).

Derive a REQ key: `REQ-F-{UPPER_SLUG}-001` where `{UPPER_SLUG}` is a 2-4 word abbreviation
(e.g. `REQ-F-AUTH-001` for "user authentication").

Ask to confirm the key.

If the REQ key is not yet in `gtl_spec/packages/<slug>.py` Package.requirements, note it — the
user should add it before the feature can be tracked by `check-req-coverage`.

### Step 4 — Write the feature vector

Create `.ai-workspace/features/active/{REQ_KEY}.yml`:

```yaml
id: {REQ_KEY}
title: {feature title}
status: active
satisfies:
  - {REQ_KEY}
intent: |
  {one paragraph describing what this feature does and why}
acceptance_criteria:
  - {criterion 1}
  - {criterion 2}
```

The `satisfies:` field is required — it is what `check-req-coverage` scans.

### Step 5 — Confirm and hand off

Show the user:

```
Created: .ai-workspace/features/active/{REQ_KEY}.yml
REQ key: {REQ_KEY}  [add to Package.requirements in gtl_spec/packages/<slug>.py]

Run: /gen-start --auto --human-proxy
```

If the REQ key is new, remind them to add it to the `requirements=[...]` list in the
Package definition so `check-req-coverage` can enforce full traceability.
