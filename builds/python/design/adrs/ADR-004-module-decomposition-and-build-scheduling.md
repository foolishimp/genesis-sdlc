**Implements**: REQ-F-MDECOMP-001, REQ-F-MDECOMP-002, REQ-F-MDECOMP-003, REQ-F-MDECOMP-004, REQ-F-MDECOMP-005

# ADR-004: Module Decomposition and Build Scheduling

**Status**: Accepted
**Date**: 2026-03-19
**Addresses**: INT-002 — insert `module_decomp` between `design` and `code`

---

## Context

The current `design→code` edge is a single large leap. Design produces ADRs and interface specifications; code implements them. This conflates two distinct concerns:

1. **Structural decomposition**: what modules exist, what are their interfaces, what depends on what
2. **Construction**: how each module is implemented

`feature_decomp` already resolves an analogous tension between requirements and design — it decomposes WHAT into trackable units before HOW is decided. `module_decomp` applies the same discipline between design and code.

The bootloader §XIV standard profile explicitly includes this node:
```
... → design → module_decomp → basis_projections → code ↔ unit_tests → ...
```

V1 collapses `basis_projections` (per V1_DOCTRINE) but adds `module_decomp`.

---

## Decision

Insert a `module_decomp` asset and two new edges into the genesis_sdlc graph:

```
design → module_decomp → code ↔ unit_tests
```

`module_decomp` is produced by the `design→module_decomp` edge and consumed by `module_decomp→code`. The existing `design→code` edge is replaced.

---

## Asset: `module_decomp`

**ID format**: `MOD-{SEQ}`

**Markov conditions** (acceptance criteria):
- `all_features_assigned` — every feature in `feature_decomp` is assigned to ≥1 module
- `dependency_dag_acyclic` — the module dependency graph contains no cycles
- `build_order_defined` — each module carries an integer `rank` (1 = leaf, N = root)

**Output artifacts**: `.ai-workspace/modules/*.yml`, one per module.

**Module YAML schema**:
```yaml
id: MOD-001
name: <module_name>
description: <what this module does>
implements_features:
  - REQ-F-*           # features this module contributes to
dependencies:
  - MOD-xxx           # modules this module imports from
rank: 1               # 1 = no dependencies (leaf), higher = depends on more modules
interfaces:
  - <interface name>: <brief contract description>
source_files:
  - builds/python/src/genesis_sdlc/<file>.py
```

---

## Edge: `design→module_decomp`

**Evaluators**:

| Evaluator | Type | Description |
|-----------|------|-------------|
| `module_coverage` | F_D | Every feature in `.ai-workspace/features/` is assigned to ≥1 module in `.ai-workspace/modules/`. Computed by grep — no LLM required. |
| `module_schedule` | F_P | Agent decomposes design ADRs into modules, assigns features, computes dependency graph, ranks build order leaf-to-root. Writes `.ai-workspace/modules/*.yml`. |
| `schedule_approved` | F_H | Human confirms: module boundaries are clean, dependency DAG is acyclic, build order is sensible, no circular dependencies. |

**F_D gates F_P**: `module_coverage` must pass before `schedule_approved` is requested. Same bootstrap pattern as `req_coverage` gates `decomp_complete`.

**Context**: `bootloader`, `genesis_sdlc_spec`, `design_adrs`, `features_dir`

---

## Edge: `module_decomp→code`

Replaces the existing `design→code` edge. Source asset changes from `design` to `module_decomp`. All other evaluators (`impl_tags`, `code_complete`) are unchanged.

The agent writes code module-by-module in `rank` order (rank=1 first). Each module's source file carries `# Implements: REQ-F-*` tags matching the module's `implements_features` list.

---

## New Context: `modules_dir`

```python
modules_dir = Context(
    name="modules_dir",
    locator="workspace://.ai-workspace/modules/",
    digest="sha256:" + "0" * 64,  # PENDING
)
```

Loaded at `module_decomp→code` so the agent knows the build schedule.

---

## Interfaces

The `module_decomp` asset is tech-agnostic — it describes module boundaries and dependencies in terms of the design, not implementation language. The `.yml` artifacts are the stable interface between the design edge and the code edge.

No implementation details (import paths, class names, function signatures) appear in `module_decomp` artifacts. Those belong in code.

---

## Consequences

**Positive**:
- Code is written in dependency order — no rework from upstream interface changes
- Module boundaries are human-approved before construction starts
- `module_coverage` F_D closes the traceability gap: every feature is assigned before code starts
- Graph now matches the bootloader §XIV standard profile (minus basis_projections)

**Trade-offs**:
- One additional F_H gate added (`schedule_approved`) — adds one human touch-point per feature cycle
- Bootstrap problem: `module_coverage` F_D blocks `module_schedule` F_P until at least one module YAML exists (same as `req_coverage`/`decomp_complete` — resolved by the same manual bootstrap pattern)
