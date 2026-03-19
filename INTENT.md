# Intent: genesis_sdlc

**ID**: INT-001
**Status**: Approved

## Problem

Building software with AI assistance is effective but unstructured. Teams use LLMs as code generators but have no formal convergence criteria — no way to know when a stage is genuinely complete, no traceability from intent to runtime, and no mechanism to detect when the codebase has drifted from its specification.

The result: fast starts, slow middles, brittle ends. AI accelerates construction but does not provide the discipline to know when construction is done.

## Value Proposition

genesis_sdlc is an AI-augmented SDLC tool built on abiogenesis (the GTL engine). It gives teams a structured, convergence-driven way to build software with AI:

- **Convergence guarantees** — every stage has explicit acceptance criteria (evaluators). Work is not done until evaluators pass.
- **Traceability** — REQ keys thread from intent through requirements, features, design, code, and tests. Coverage is computable at any time.
- **AI in the right role** — deterministic checks (F_D) run first; agent assessment (F_P) only runs when deterministic checks pass; human approval (F_H) gates stage transitions. No wasted agent calls.
- **Event-sourced state** — all progress is recorded in an append-only event log. State is derived from events, not mutable objects. Recovery is replay.

## Scope (V1)

genesis_sdlc V1 covers the bootstrap SDLC graph:

```
intent → requirements → feature_decomp → design → code ↔ unit_tests
```

- A team installs genesis_sdlc into their project (bootstrapped via gen-install)
- They define their project's Package (assets, edges, evaluators) in a GTL spec
- The engine drives construction through the graph, enforcing convergence at each edge
- Human approval gates at spec/design boundaries prevent premature progression
- REQ key traceability is enforced by deterministic checks at every code edge

## Out of Scope (V1)

- UAT tests, CI/CD, telemetry (V2 graph extensions)
- Multi-agent coordination (single claude_code worker in V1)
- GUI or web interface (CLI only in V1)
- Package distribution (local install via gen-install only in V1)

---

# Intent: Module Decomposition and Build Scheduling

**ID**: INT-002
**Status**: Approved

## Problem

The current `design→code` edge is a single large leap. Design produces ADRs and interface specifications, but the next step — writing code — requires the agent to simultaneously decide module boundaries, dependency order, and implementation. This conflates two distinct concerns: *what modules exist and in what order they must be built* (structural decomposition) versus *how each module is implemented* (construction).

The result: code produced from design tends to be under-decomposed or built in an order that requires rework when upstream modules change.

## Value Proposition

Insert a `module_decomp` asset and two new edges between `design` and `code`:

```
design → module_decomp → code ↔ unit_tests
```

`module_decomp` decomposes the design into a ranked module dependency graph — the same discipline that `feature_decomp` brings to requirements. The agent (and the human) approve a build schedule before any code is written. Modules are built leaf-first (no dependencies) through to root (depends on everything), so each module can be implemented against stable interfaces.

This completes the standard SDLC profile from the bootloader §XIV:
```
... → design → module_decomp → code ↔ unit_tests → ...
```

## Scope

- New asset: `module_decomp` with markov conditions: `all_features_assigned`, `dependency_dag_acyclic`, `build_order_defined`
- New edge: `design→module_decomp` with F_P (decompose) + F_H (approve schedule) evaluators
- Modified edge: `design→code` replaced by `module_decomp→code`
- New F_D evaluator: `module_coverage` — every design feature assigned to ≥1 module
- Output artifacts: `.ai-workspace/modules/*.yml` — one per module, with declared dependencies and build rank

## Out of Scope

- Basis projections (V3 — further decomposition below module level)
- Parallel build scheduling (single worker in V1)
