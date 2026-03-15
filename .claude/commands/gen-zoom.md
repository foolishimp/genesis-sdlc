# /gen-zoom - Graph Edge Zoom

Zoom into or out of graph edges, revealing sub-structure within an edge traversal or aggregating across edges for a high-level view. The graph is zoomable (§1) — this command navigates zoom levels.

<!-- Implements: REQ-GRAPH-002 (Zoomable Graph), REQ-UX-007 (Edge Zoom Management) -->
<!-- Reference: AI_SDLC_ASSET_GRAPH_MODEL.md §1, §2.5 (Graph Scaling), ADR-009 (Graph Topology as Config) -->

## Usage

```
/gen-zoom [in|out|show] --edge "{source}→{target}" [--feature "REQ-F-*"] [--depth {n}]
```

| Option | Description |
|--------|-------------|
| `in` | Zoom into an edge — show sub-steps and internal structure |
| `out` | Zoom out — show aggregated view across multiple edges |
| `show` | Show current zoom level and available zoom targets (default) |
| `--edge` | The edge to zoom into/out of |
| `--feature` | Scope to a specific feature (optional) |
| `--depth` | How many levels to zoom (default: 1) |

## Instructions

### Step 1: Load Graph Context

1. Read `config/graph_topology.yml` — the current topology
2. Read the feature vector if `--feature` is provided
3. Read edge configuration from `config/edge_params/{edge}.yml`

### Step 2: Show Current Zoom Level (default / `show`)

Display the current graph topology with indicators of which edges have sub-structure:

```
═══ GRAPH ZOOM — Current View ═══

intent → requirements → design → code ↔ unit_tests → uat_tests → cicd → running_system → telemetry
                                                                                          ↓
                                                                                        intent (feedback)

Zoomable edges (have internal sub-structure):
  [+] intent→requirements     3 sub-steps: capture, structure, validate
  [+] requirements→design     4 sub-steps: ADR decisions, constraint resolution, architecture, design doc
  [+] design→code             3 sub-steps: scaffold, implement, integrate
  [+] code↔unit_tests         3 sub-steps: red, green, refactor (TDD cycle)
  [ ] uat_tests               1 step (flat)
  [ ] cicd                    1 step (flat)

Current feature zoom:
  REQ-F-AUTH-001: at design→code (sub-step: implement)
  REQ-F-API-001: at requirements (sub-step: validate)

═══════════════════════════
```

### Step 3: Zoom In

Reveal the internal structure of an edge. Each edge decomposes into sub-steps that are themselves mini-iterations:

#### intent→requirements

```
═══ ZOOM: intent→requirements ═══

Sub-steps:
  1. CAPTURE    — Extract requirements from intent (functional + non-functional)
                  Input: INTENT.md
                  Output: Draft requirements list
                  Evaluator: agent (completeness check)

  2. STRUCTURE  — Organise into REQ-F-* and REQ-NFR-* keys
                  Input: Draft requirements
                  Output: Structured requirements with IDs
                  Evaluator: deterministic (format check) + agent (gap check)

  3. VALIDATE   — Human confirms requirements capture intent faithfully
                  Input: Structured requirements
                  Output: Approved requirements
                  Evaluator: human (gradient check via /gen-spec-review)

{Feature zoom if --feature provided:}
  REQ-F-AUTH-001:
    [✓] capture    — 5 functional, 2 non-functional extracted
    [✓] structure  — REQ-F-AUTH-001, REQ-F-AUTH-002, REQ-NFR-SEC-001
    [●] validate   — pending human review

═══════════════════════════
```

#### requirements→design

```
═══ ZOOM: requirements→design ═══

Sub-steps:
  1. ADR_DECISIONS     — Make technology binding decisions
                         Output: ADR documents
                         Evaluator: human (design approval)

  2. CONSTRAINT_RESOLVE — Resolve mandatory constraint dimensions
                          Output: project_constraints.yml populated
                          Evaluator: deterministic (all mandatory fields filled)

  3. ARCHITECTURE       — Define module decomposition and integration points
                          Output: Architecture diagrams, module map
                          Evaluator: agent (coherence with requirements)

  4. DESIGN_DOC         — Produce consolidated design document
                          Output: Design document with REQ key traceability
                          Evaluator: agent + human (gradient check)

═══════════════════════════
```

#### design→code

```
═══ ZOOM: design→code ═══

Sub-steps:
  1. SCAFFOLD    — Create file structure, module boundaries, build config
                   Evaluator: deterministic (builds, lints)

  2. IMPLEMENT   — Write production code with Implements: REQ-* tags
                   Evaluator: deterministic (compile, lint) + agent (design alignment)

  3. INTEGRATE   — Wire modules together, verify cross-module contracts
                   Evaluator: deterministic (integration tests) + agent (architecture check)

═══════════════════════════
```

#### code↔unit_tests (TDD cycle)

```
═══ ZOOM: code↔unit_tests (TDD co-evolution) ═══

Sub-steps (cyclical):
  1. RED       — Write failing test for next requirement
                 Validates: REQ-* tag in test
                 Evaluator: deterministic (test fails as expected)

  2. GREEN     — Write minimal code to pass the test
                 Implements: REQ-* tag in code
                 Evaluator: deterministic (test passes)

  3. REFACTOR  — Improve code structure without changing behaviour
                 Evaluator: deterministic (all tests still pass) + agent (structural quality)

  Cycle repeats until all REQ keys for this feature have tests.

═══════════════════════════
```

### Step 4: Zoom Out

Aggregate multiple edges into a higher-level view:

```
═══ ZOOM OUT — Feature-Level View ═══

REQ-F-AUTH-001 "User authentication"
  Specification:  ████████████████████ 100% (intent + req + design converged)
  Construction:   █████████░░░░░░░░░░░  45% (code in progress, tests started)
  Validation:     ░░░░░░░░░░░░░░░░░░░░   0% (UAT + CI/CD pending)
  Operations:     ░░░░░░░░░░░░░░░░░░░░   0% (telemetry pending)

REQ-F-DB-001 "Database schema"
  Specification:  ████████████████████ 100%
  Construction:   ████████████████████ 100%
  Validation:     ██████████░░░░░░░░░░  50%
  Operations:     ░░░░░░░░░░░░░░░░░░░░   0%

═══════════════════════════
```

The four aggregation bands map to graph regions:
- **Specification**: intent + requirements + design
- **Construction**: code + unit_tests
- **Validation**: uat_tests + cicd
- **Operations**: running_system + telemetry

### Step 5: Graph Discovery Connection (§2.5)

When zooming in reveals that an edge's sub-structure is consistently too complex (many sub-steps, high iteration counts), this is a signal for graph discovery — the edge may need to be split into separate edges in the topology.

If zoom-in reveals:
- More than 5 sub-steps within a single edge
- Sub-steps that are independently convergence-tested
- Sub-steps that have different evaluator compositions

Then surface a recommendation:

```
Graph Discovery Signal:
  Edge design→code has 5 sub-steps with independent convergence.
  Consider splitting into: design→scaffold, scaffold→implement, implement→integrate
  Run /gen-escalate to capture as intent if warranted.
```

This is the tolerance pressure (ADR-016) operating on graph topology complexity.

## Zoom State Management

<!-- Implements: REQ-UX-007 (Edge Zoom Management) -->

When the user zooms in on an edge, the zoom state is persisted so that:
1. The same sub-graph is shown on subsequent `/gen-zoom show` calls without re-specifying the edge
2. Zoomed edges are tracked to prevent double-iteration at two levels simultaneously
3. Fold-back collapses sub-graph results back to the parent edge cleanly

### zoom_state.yml — Zoom State File

Zoom state is tracked in `.ai-workspace/spec/zoom_state.yml`. This file is a **derived view** — it can be reconstructed from `edge_zoomed` and `edge_folded_back` events in the event log.

```yaml
# .ai-workspace/spec/zoom_state.yml
# Tracks which edges are currently zoomed in (expanded to sub-graph)
# Managed by /gen-zoom; read by /gen-iterate and /gen-start

version: "1.0.0"
updated_at: "{ISO 8601}"

zoomed_edges:
  - edge: "requirements→design"
    feature: "REQ-F-AUTH-001"        # null = global zoom (all features)
    zoomed_at: "{ISO 8601}"
    sub_steps:
      - id: "ADR_DECISIONS"
        status: "converged"
      - id: "CONSTRAINT_RESOLVE"
        status: "iterating"
      - id: "ARCHITECTURE"
        status: "pending"
      - id: "DESIGN_DOC"
        status: "pending"
    parent_edge_status: "iterating"   # status to restore on fold-back
```

### Zoom-In Protocol

When `gen-zoom in --edge "{edge}" [--feature "REQ-F-*"]` is invoked:

1. **Read current zoom state** from `.ai-workspace/spec/zoom_state.yml`
2. **Check for double-zoom**: if the edge is already in `zoomed_edges`, reject with:
   ```
   Error: edge "requirements→design" is already zoomed in.
   Run /gen-zoom out --edge "requirements→design" (fold-back) before zooming again.
   ```
3. **Build sub-step list** from the edge's internal structure (as shown in Step 3 above)
4. **Write to zoom_state.yml**: add entry to `zoomed_edges` with `status: pending` for each sub-step
5. **Emit `edge_zoomed` event**:
   ```json
   {
     "event_type": "edge_zoomed",
     "timestamp": "{ISO 8601}",
     "project": "{project name}",
     "feature": "{REQ-F-* or null}",
     "edge": "{source}→{target}",
     "data": {
       "sub_steps": ["{step_id}", "..."],
       "zoom_depth": 1
     }
   }
   ```
6. Display the zoomed sub-graph (Step 3 output)

### Fold-Back (Zoom-Out) Protocol

When `gen-zoom out --edge "{edge}" [--feature "REQ-F-*"]` is invoked:

1. **Read zoom_state.yml** — find the entry for this edge
2. **If edge is not zoomed**: report "edge is not zoomed; nothing to fold back"
3. **Collect sub-step results**: read statuses from `zoomed_edges[edge].sub_steps`
4. **Compute parent edge status**: if all sub-steps are `converged` → parent edge becomes `converged`; otherwise `iterating`
5. **Update parent edge**: propagate the fold-back result to the feature vector's trajectory
6. **Remove from zoom_state.yml**: delete the entry for this edge
7. **Emit `edge_folded_back` event**:
   ```json
   {
     "event_type": "edge_folded_back",
     "timestamp": "{ISO 8601}",
     "project": "{project name}",
     "feature": "{REQ-F-* or null}",
     "edge": "{source}→{target}",
     "data": {
       "sub_steps_converged": {n},
       "sub_steps_total": {n},
       "parent_edge_result": "converged|iterating"
     }
   }
   ```
8. Display the collapsed view (Step 4 output)

### Interaction with /gen-iterate

`/gen-iterate` reads `zoom_state.yml` before proceeding:
- If the requested edge is in `zoomed_edges`, print a warning:
  ```
  Warning: edge "requirements→design" is zoomed in (sub-step level).
  Iterating at the parent edge level while zoomed may double-count work.
  Options:
    1. Continue iterating at parent level (suppress this warning with --ignore-zoom)
    2. Switch to sub-step iteration: /gen-iterate --edge "requirements→design:ARCHITECTURE"
    3. Fold back first: /gen-zoom out --edge "requirements→design"
  ```
- The user can override with `--ignore-zoom` to proceed despite the zoom lock

### zoom_state.yml Lifecycle

- **Created**: on first `/gen-zoom in` call (if file does not exist)
- **Updated**: on every zoom-in or fold-back operation
- **Reset**: on `/gen-zoom out --all` (clears all zoomed edges)
- **Reconstructable**: from `edge_zoomed` and `edge_folded_back` events in `events.jsonl`

## Event Emission

Zoom-show and zoom-out (read-only view) emit no events. Zoom-in and fold-back **do** emit events, because they modify workspace state:

| Operation | Event emitted |
|-----------|--------------|
| `/gen-zoom in` | `edge_zoomed` |
| `/gen-zoom out` (fold-back) | `edge_folded_back` |
| `/gen-zoom show` | (none — read-only) |

Exception: If zoom reveals a graph discovery signal (Step 5), it surfaces the signal but does NOT emit an intent. The human decides whether to escalate via `/gen-escalate`.
