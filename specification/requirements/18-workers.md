# Worker Assignment Requirements

**Family**: REQ-F-WORKER-*
**Status**: Active
**Category**: Runtime Control

This family defines how genesis_sdlc exposes and uses multiple workers over the assurance control plane.

### REQ-F-WORKER-001 — The installed runtime exposes declared workers and default role assignments

The product must expose worker configuration as an installed runtime surface rather than leaving it implicit in code or environment defaults.

**Acceptance Criteria**:
- AC-1: `.gsdlc/release/runtime/` ships a machine-readable worker registry and default role-assignment surface
- AC-2: Each declared worker entry names the worker id, the roles it can satisfy, and the backend or adapter binding it uses
- AC-3: The shipped worker surface is not conforming if it hardcodes the product to one concrete worker only
- AC-4: Graph role definitions remain constitutional workflow law; worker declarations remain runtime configuration
- AC-5: For `0.9.9`, declared workers may assume their bound CLI/runtime is already installed and authenticated; worker declaration does not itself require backend provisioning logic

### REQ-F-WORKER-002 — The control plane resolves role-to-worker-to-backend assignment

Worker choice must be compiled through the control plane rather than being inferred separately by each command or harness.

**Acceptance Criteria**:
- AC-1: The resolved runtime records the winning `role -> worker -> backend` mapping for each live constructive role
- AC-2: Runtime or session overrides for worker assignment live under `.ai-workspace/runtime/`, not under project-truth specification surfaces
- AC-3: Unknown workers, unknown backends, or role assignments that violate declared worker role coverage fail as runtime misconfiguration
- AC-4: The resolved runtime records provenance for each winning assignment, including source layer and source path
- AC-5: In the steady-state worker model, backend identity is derived from the winning worker assignment; standalone backend selection is not a co-equal operative authority

### REQ-F-WORKER-003 — Commands and qualification bind the resolved worker assignment

Product commands and qualification must use the resolved worker assignment as the operative selection surface.

**Acceptance Criteria**:
- AC-1: Product commands bind the active worker for an `F_P` turn from the resolved runtime rather than from a hardcoded singleton worker or backend default
- AC-2: Live qualification binds the active worker through the same resolved runtime path used by product commands
- AC-3: Runtime gating for live qualification occurs after runtime resolution, not from ad hoc environment defaults alone
- AC-4: Changing worker assignment does not require graph or evaluator changes

### REQ-F-WORKER-004 — Engine build identity, worker identity, and backend identity remain distinct provenance surfaces

The system must stop overloading one identity field to mean engine, worker, and backend simultaneously.

**Acceptance Criteria**:
- AC-1: Archives and runtime evidence distinguish engine build identity, assigned worker identity, and transport backend identity
- AC-2: If those provenance surfaces disagree, the archive reports the mismatch explicitly rather than silently collapsing them
- AC-3: A successful live run can answer which worker and which backend closed each constructive edge
- AC-4: The product does not treat engine build identity as sufficient provenance for worker attribution

### REQ-F-WORKER-005 — The worker model is multi-vendor and extensible

Multiple workers must be treated as first-class runtime citizens rather than as one-off special cases.

**Acceptance Criteria**:
- AC-1: The active runtime can declare and exercise at least two concrete workers through one common control-plane path
- AC-2: Adding a new worker that binds to a conforming backend adapter does not require changes to graph law
- AC-3: Worker capability differences are surfaced through declared capabilities and role coverage, not by baking vendor-specific logic into the lifecycle graph
- AC-4: The product remains free to bind one worker at a time per traversal, but that binding must come from the resolved worker-assignment model rather than from a hardcoded runtime singleton
- AC-5: The `0.9.9` worker model standardizes invocation and provenance across vendors, but does not require the product to install or authenticate those vendor CLIs itself
