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

---

# Intent: Integration Tests and User Guide as First-Class Graph Assets

**ID**: INT-003
**Status**: Approved

## Problem

Two assets that should be on the convergence blocking path are currently outside the graph:

**Integration tests (sandbox e2e)**: The sandbox e2e run is embedded inside `uat_tests` as an F_P evaluator. This conflates two distinct concerns — *did the tests pass in a real environment?* (deterministic, repeatable) and *does a human accept the release?* (judgment). A sandbox report is a structured artifact, not a human decision. Treating it as F_P rather than F_D means it can be skipped or bypassed, and its results carry no independent convergence certificate.

**User guide**: `REQ-F-DOCS-001` is listed in requirements and has a feature YAML, but `user_guide` is not an asset in the graph. No F_D evaluator checks it. No F_P evaluator certifies it. Drift is already visible — `USER_GUIDE.md` says v0.1.3 while the codebase is at v0.2.0. A REQ key with no graph binding is unenforceable.

## Value Proposition

Insert two new assets into the graph between `unit_tests` and `uat_tests`:

```
code ↔ unit_tests → integration_tests → user_guide → uat_tests
```

**`integration_tests`**: Sandbox install + `pytest -m e2e` run. Produces a structured report (`sandbox_report.json`). F_D checks the report exists and `all_pass: true`. F_P runs the sandbox and writes the report. Convergence is deterministic — no human judgment required.

**`user_guide`**: Documentation asset. F_D checks version string matches release version and `<!-- Covers: REQ-* -->` tags are present for all operator-facing REQ keys. F_P certifies the guide answers install, first session, commands, operating loop, and recovery paths coherently.

**`uat_tests`**: Simplified to a pure F_H gate. Human reviews the integration test report and the guide before approving the release. Nothing ships without both.

This completes the constitutional path: code and tests → proven in a real environment → documented → human approved.

## Scope

- New asset: `integration_tests` with markov: `sandbox_install_passes`, `e2e_scenarios_pass`
- New asset: `user_guide` with markov: `version_current`, `req_coverage_tagged`, `content_certified`
- New edge: `unit_tests→integration_tests` — F_D (sandbox report check) + F_P (sandbox runner)
- New edge: `integration_tests→user_guide` — F_D (version tag + REQ coverage tags) + F_P (content coherence)
- Modified edge: `integration_tests→uat_tests` (was `unit_tests→uat_tests`) — F_H only; F_D sandbox check moves to integration_tests
- Sandbox report path: `.ai-workspace/uat/sandbox_report.json` (unchanged)
- Guide traceability tags: `<!-- Covers: REQ-F-* -->` in `docs/USER_GUIDE.md`
- New REQ keys: REQ-F-DOCS-002 (guide on blocking path), REQ-F-UAT-002 (integration_tests asset), REQ-F-UAT-003 (uat_tests as pure F_H gate)

## Out of Scope

- Rewriting USER_GUIDE.md content (only adding traceability tags and version bump)
- Multiple guide formats or outputs (single markdown file)
- Automated guide generation
