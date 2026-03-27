# Backlog Requirements

**Family**: REQ-F-BACKLOG-*
**Status**: Still needed
**Category**: Capability

Backlog requirements define the pre-intent holding area for signals that are not yet formalized as intent.

### REQ-F-BACKLOG-001 — Backlog schema and directory convention

**Acceptance Criteria**:
- AC-1: `.ai-workspace/backlog/BL-*.yml` files follow a defined YAML schema with fields: `id`, `title`, `description`, `status`, `priority`, `created`, `signal_source`
- AC-2: Status values: `draft`, `ready`, `promoted`, `deferred`
- AC-3: Directory is created by the installer as part of workspace bootstrap

### REQ-F-BACKLOG-002 — Sensory system surfaces ready items

**Acceptance Criteria**:
- AC-1: `gen-gaps` and `gen-status` output includes a count of ready backlog items
- AC-2: Ready items are those with `status: ready`
- AC-3: The backlog serves as the pre-intent holding area — ideas in gestation before formal intent

### REQ-F-BACKLOG-003 — gen backlog list

**Acceptance Criteria**:
- AC-1: `gen backlog list` shows all backlog items with id, title, status, and priority
- AC-2: Output is human-readable with optional `--json` for machine consumption

### REQ-F-BACKLOG-004 — gen backlog promote

**Acceptance Criteria**:
- AC-1: `gen backlog promote BL-xxx` emits an `intent_raised` event with `signal_source: backlog`
- AC-2: Marks the backlog item as `status: promoted`
- AC-3: The promoted item enters the normal homeostatic loop
