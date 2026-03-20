# ADR-011: Backlog Schema and Command Interface

**Status**: Accepted
**Date**: 2026-03-21
**Implements**: REQ-F-BACKLOG-001, REQ-F-BACKLOG-002, REQ-F-BACKLOG-003, REQ-F-BACKLOG-004

## Context

Ideas in gestation need a holding area before formal intent. The backlog is the pre-intent buffer — signals from sensory systems, bug post-mortems, and operator observations accumulate here before promotion to the homeostatic loop.

## Decision

### Schema (REQ-F-BACKLOG-001)

`.ai-workspace/backlog/BL-*.yml` with fields:

```yaml
id: BL-001
title: "Short description"
description: "Detailed rationale"
status: draft | ready | promoted | deferred
priority: high | medium | low
created: "2026-03-21T00:00:00Z"
signal_source: operator | bug_post_mortem | sensory | agent
```

Directory created by the installer as part of workspace bootstrap.

### Surfacing (REQ-F-BACKLOG-002)

`gen-gaps` and `gen-status` include a count of `status: ready` items. The backlog is the sensory system's output buffer — observations that haven't yet become intents.

### Commands (REQ-F-BACKLOG-003, REQ-F-BACKLOG-004)

`gen backlog list` — shows all items with id, title, status, priority. Optional `--json`.

`gen backlog promote BL-xxx` — emits `intent_raised{signal_source: backlog}` event, sets `status: promoted`. The promoted item enters the normal homeostatic loop.

## Tech Stack

- YAML files in `.ai-workspace/backlog/`
- Commands in abiogenesis engine (`genesis/commands.py`)
- Event integration via `intent_raised` prime operator

## Consequences

- Low ceremony — a YAML file is the minimum viable artifact
- Backlog items are not graph assets — they live outside the convergence path until promoted
- Promotion is the bridge from observation to intent
