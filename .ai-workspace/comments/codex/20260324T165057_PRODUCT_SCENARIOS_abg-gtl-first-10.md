# Product Scenarios: ABG + GTL

**Status**: First attempt
**Date**: 2026-03-24
**Purpose**: Product-owner scenario set for validating that ABG + GTL are logically complete before formal test-case derivation

## Framing

These scenarios are not unit tests.

They are product scenarios:

- what the product owner needs the system to be able to do
- what GTL must be able to express
- what ABG must be able to execute
- what the event stream, projection, and delta must be able to explain

They are intentionally ordered from simple to complex.

---

## Scenario 1: Single-Edge Happy Path

**Need**

As product owner, I need the system to take one coarse edge from unmet to converged through the normal ABG loop.

**Given**

- A GTL Package with one edge: `design→code`
- The edge has an F_P evaluator such as `code_complete`
- No prior convergence events exist

**When**

ABG runs one iteration and the actor produces acceptable output.

**Then**

- ABG emits `run_started`
- ABG emits `edge_started`
- ABG emits `fp_dispatched`
- ABG later records `assessed{kind: fp, result: pass}`
- ABG emits `edge_converged`
- `delta(design→code) = 0`

**Confirms**

- Minimal traversal works end to end
- GTL can express the edge
- ABG can execute the loop
- Projection and delta agree with the result

---

## Scenario 2: Deterministic Gap Blocks False Progress

**Need**

As product owner, I need deterministic failures to block progress when no lawful construction path exists.

**Given**

- An edge with an F_D evaluator such as `impl_tags`
- The workspace violates the deterministic rule
- No lawful F_P remediation path exists for this failure

**When**

ABG evaluates the edge.

**Then**

- ABG emits `found{kind: fd_gap}`
- ABG does not emit `fp_dispatched`
- ABG does not emit `edge_converged`
- Delta remains positive

**Confirms**

- F_D is authoritative
- The engine fails closed
- Deterministic truth is not bypassed by construction

---

## Scenario 3: Deterministic Findings Escalate to Constructive Work

**Need**

As product owner, I need deterministic findings to become the construction surface when an F_P path exists.

**Given**

- An edge with both F_D and F_P evaluators
- F_D fails
- The edge has a lawful F_P path to repair the problem

**When**

ABG iterates.

**Then**

- ABG emits `found{kind: fd_findings}`
- ABG emits `fp_dispatched`
- The F_P manifest includes the F_D findings
- The system does not incorrectly stop at `fd_gap`

**Confirms**

- Escalation is lawful
- F_D truth is preserved inside F_P work
- ABG can turn deterministic findings into bounded construction

---

## Scenario 4: Human Judgment Gates Final Convergence

**Need**

As product owner, I need human approval to remain a first-class gate where required.

**Given**

- An edge with F_D, F_P, and F_H evaluators
- F_D and F_P are satisfied
- Human approval is still required

**When**

ABG evaluates the edge before approval, and then after approval.

**Then**

- Before approval, ABG emits `fh_gate_pending`
- The edge does not converge yet
- After `approved{kind: fh_review}`, the edge converges

**Confirms**

- Human judgment is not flattened into automation
- F_H remains durable and explicit
- The system can stop lawfully for human review

---

## Scenario 5: Two Work Lines Share One Topology but Converge Independently

**Need**

As product owner, I need multiple work lines on the same topology to remain independent.

**Given**

- Two active work lines on the same edge, e.g. `REQ-F-AUTH` and `REQ-F-BILLING`
- Same GTL Package and same edge topology

**When**

AUTH converges before BILLING.

**Then**

- AUTH gets its own `edge_converged`
- BILLING still has positive delta
- AUTH certificates do not satisfy BILLING queries
- The edge can be converged for one work line and unconverged for another

**Confirms**

- `work_key` is real identity, not annotation
- Convergence is scoped by work line
- Shared topology does not collapse independent work

---

## Scenario 6: Workflow Upgrade Preserves Lineage Correctly

**Need**

As product owner, I need workflow upgrades to preserve lawful history without silently accepting stale truth.

**Given**

- A prior workflow version `v1`
- A current workflow version `v2`
- Prior `approved` and `assessed` events from `v1`

**When**

ABG evaluates the same work under `v2`.

**Then**

- Prior F_P does not satisfy if the `spec_hash` changed
- Prior F_H satisfies only if manifest carry-forward explicitly allows it
- History remains in the event stream
- Delta is computed under the current provenance lens

**Confirms**

- Provenance is constitutional
- Workflow upgrades are explicit, not silent
- Carry-forward is lawful and scoped

---

## Scenario 7: Reset Re-Opens Certification Without Destroying History

**Need**

As product owner, I need a way to force re-certification of possibly stale work without losing audit history.

**Given**

- A converged work line
- Another independent work line on the same edge

**When**

A scoped `reset` is emitted for one work line.

**Then**

- F_P certifications before the boundary are shadowed for that scope
- Re-certification must occur after the boundary
- F_H persists unless explicitly revoked
- Sibling work lines remain unaffected
- All prior events remain in the log

**Confirms**

- Correction is additive, not rollback-shaped
- Reset is scoped
- The event log remains truthful

---

## Scenario 8: A Coarse Edge Is Locally Refined by Zoom

**Need**

As product owner, I need the system to refine one coarse edge into a richer lawful subgraph when the work demands it.

**Given**

- A coarse edge `design→code`
- A GTL Fragment such as `design→module_decomp→code_units→code`
- A work line complex enough to require refinement

**When**

That edge is zoomed for the work line.

**Then**

- The original coarse edge is replaced by the fragment internals for that work
- A `zoomed` event records the refinement
- Outer convergence becomes the aggregate of internal convergence
- The outer contract is preserved: the system still produces `code`

**Confirms**

- GTL can express local lawful refinement
- ABG can reason over refined structure
- Refinement is structural, not ad hoc mutation

---

## Scenario 9: Parent Work Decomposes into Child Work and Folds Back

**Need**

As product owner, I need larger work to decompose recursively and only converge when its children converge.

**Given**

- A parent work line such as `REQ-F-AUTH`
- Spawned child work lines such as `REQ-F-AUTH/login` and `REQ-F-AUTH/signup`

**When**

One child converges and another does not.

**Then**

- The parent remains unconverged
- Child lineage is visible via `work_spawned`
- Only when all descendants converge does the parent converge

**Confirms**

- Recursive work identity is real
- Fold-back is event-sourced
- Parent convergence is a projection over descendants

---

## Scenario 10: An In-Flight Run Is Retried or Superseded Safely

**Need**

As product owner, I need execution attempts to be governed reliably so stale or failed attempts do not corrupt convergence.

**Given**

- One work line on one edge
- A first run attempt is already in flight

**When**

The first attempt times out, fails transport, or is superseded by a second run.

**Then**

- The event stream records attempt identity explicitly
- The live run is distinguishable from stale runs
- A later stale result is recorded but not applied
- A new run may proceed lawfully after timeout/failure/supersession
- Convergence is attributed only to the valid live attempt

**Confirms**

- Run governance is strong enough for reliable execution
- Retries preserve history
- Supersession does not erase truth but prevents stale application

---

## Scenario 11: A Named Discovery Workflow Is Reusable as a Graph Function

**Need**

As product owner, I need GTL to express a reusable discovery process as a named workflow, not just as a one-off fragment.

**Given**

- A named graph function such as `discovery_workflow()`
- The function returns a Fragment with a shape like:
  - `intent→discovery_plan`
  - `discovery_plan→discovery_code`
  - `discovery_code→synthesized_results`
- A coarse outer edge such as `intent→synthesized_results`

**When**

ABG zooms the coarse edge using `discovery_workflow()`.

**Then**

- The zoom references the named workflow, not anonymous inline structure
- The resulting internal edges are lawful GTL structure
- `zoomed` records which workflow was applied
- The outer contract is preserved while the internal discovery process becomes explicit

**Confirms**

- GTL can encode reusable graph-valued workflows
- Zoom can take a named workflow as a structural parameter
- Discovery can be modeled as ordinary graph structure rather than prose process

---

## Scenario 12: The Same Functional Workflow Can Be Applied at Multiple Sites

**Need**

As product owner, I need one functional workflow to be reusable at more than one point in the graph without copy-pasting topology.

**Given**

- A named graph function such as `discovery_workflow()`
- Two different coarse edges or two different work lines that both need the same discovery process

**When**

ABG applies the same workflow at both sites.

**Then**

- Both sites get distinct fragment instances with shared structure
- Their spawned child work lines remain independent
- Convergence at one site does not satisfy the other
- The workflow definition is reused, not duplicated

**Confirms**

- Graph functions are truly reusable
- ABG can execute repeated structural patterns without collapsing lineage
- Composition is structural reuse, not graph cloning by hand

---

## Scenario 13: Functional Workflows Compose Into Larger Workflows

**Need**

As product owner, I need to compose one workflow into another so larger processes can be built from smaller lawful parts.

**Given**

- A graph function `discovery_workflow(): intent→synthesized_results`
- A graph function `context_synthesis_workflow(): synthesized_results→new_context`
- A larger outer need such as `intent→new_context`

**When**

The two workflows are composed.

**Then**

- The output interface of `discovery_workflow` satisfies the input interface of `context_synthesis_workflow`
- Composition validation succeeds before runtime
- ABG can zoom the larger outer edge into the composed internal workflow
- Convergence of `intent→new_context` becomes the lawful aggregate of both sub-workflows

**Confirms**

- Graph-valued functions compose
- Interfaces are real and validated
- ABG + GTL can build larger workflows from smaller repeatable parts

---

## Scenario 14: Different Discovery Workflows Can Be Chosen as Repeatable Zoom Parameters

**Need**

As product owner, I need the system to choose different discovery workflows for different work lines without changing the outer graph contract.

**Given**

- One coarse outer edge such as `intent→new_context`
- More than one named workflow with the same interface, for example:
  - `light_discovery_workflow(): intent→new_context`
  - `deep_discovery_workflow(): intent→new_context`
- Different work lines with different complexity or risk

**When**

One work line is zoomed with the light workflow and another with the deep workflow.

**Then**

- Both workflows satisfy the same outer contract
- Each work line records which workflow was chosen
- The work lines remain comparable at the outer edge while differing internally
- ABG can reason over both because the interfaces are compatible

**Confirms**

- Workflow choice can be late-bound per work line
- Zoom parameters can be repeatable named workflows, not hardcoded one-offs
- GTL supports interchangeability at the interface level

---

## Scenario 15: Consensus Gates an Intent Event Before Promotion

**Need**

As product owner, I need multiple evaluators to gate whether an intent event is strong enough to be promoted into actionable structured intent.

**Given**

- An `intent_event` asset
- Multiple evaluator branches over that event
- A gate such as `consensus(2/3)`
- A promotion workflow such as `intent_event→intent_vector`

**When**

The evaluator branches complete and the consensus gate is applied.

**Then**

- The gate records whether the threshold was met
- Dissent is preserved rather than erased
- Promotion to `intent_vector` occurs only if the gate passes
- If the gate does not pass, the outer workflow remains unconverged

**Confirms**

- Consensus can act as a reusable higher-order gate
- Promotion is conditional and lawful
- Evaluator aggregation is part of the workflow calculus, not just edge metadata

---

## Scenario 16: An Intent Vector Fans Out the Same Discovery Workflow Across Branches

**Need**

As product owner, I need one promoted intent vector to branch into multiple discovery executions using the same reusable workflow.

**Given**

- An `intent_vector` asset containing multiple actionable intent branches
- A named graph function such as `discovery_workflow()`
- Branch work lines derived from each vector element

**When**

ABG fans out the workflow across the vector.

**Then**

- Each branch gets its own work lineage
- The same discovery workflow is reused across all branches
- Branch execution is independent
- The outer workflow does not collapse branch identity

**Confirms**

- GTL can express fan-out as higher-order workflow structure
- Reuse survives branching
- ABG can preserve branch lineage under repeated application

---

## Scenario 17: Branch Results Fan In Through a Synthesizing Reducer

**Need**

As product owner, I need multiple branch results to rejoin through a lawful reducer rather than ad hoc manual synthesis.

**Given**

- Multiple discovery branch outputs
- A reducer workflow such as `synthesize_results`
- An outer need for one `synthesized_results` asset

**When**

The branch outputs are fanned in through the reducer.

**Then**

- The reducer consumes branch outputs as an explicit interface
- The synthesized result is produced as a lawful graph output
- The parent workflow remains unconverged until the required branch set is available
- The event stream explains which branches were reduced into the result

**Confirms**

- GTL can express fan-in / reduction as first-class workflow structure
- ABG can explain rejoin semantics through events and convergence
- Synthesis is structural, not hidden imperative glue

---

## Scenario 18: A Higher-Order Discovery Pipeline Produces New Context

**Need**

As product owner, I need a complete higher-order workflow where intent is gated, promoted, fanned out into discovery, reduced back into synthesis, and finally promoted into new context.

**Given**

- `intent_event`
- `consensus` gate
- `intent_vector`
- `discovery_workflow()`
- `synthesize_results`
- `new_context`

**When**

The full higher-order workflow is applied.

**Then**

- Intent is gated before promotion
- Promotion creates a branchable vector
- Discovery fans out across the vector
- Results fan in through synthesis
- The final output is `new_context`
- Replay can explain the whole path through gate, promotion, branching, reduction, and final convergence

**Confirms**

- GTL can express higher-order workflow programs end to end
- ABG can interpret mixed branching and reducing structure lawfully
- The language is capable of wrangling deterministic, probabilistic, and judgment-bearing programs compositionally

---

## Scenario 19: A Leaf Task Executes Inside Iterate as Governed Sub-Work

**Need**

As product owner, I need bounded sub-work to execute inside a larger workflow step without forcing every small action to become a full graph edge.

**Given**

- A parent edge with F_P construction work
- A bounded leaf task with explicit input and output schema
- A parent run already in progress

**When**

The iterate step dispatches the leaf task before completing the parent F_P path.

**Then**

- The leaf task gets subordinate run identity under the parent
- Input and output are schema-validated
- Timeout or transport failure is classified without corrupting the parent lineage
- Successful output feeds the parent workflow lawfully

**Confirms**

- ABG can govern sub-work without collapsing it into opaque inline behavior
- GTL can express bounded subordinate tasks
- The engine preserves lineage even below the graph-edge level

---

## Scenario 20: Bootloader Drift Is Detected and Recovered Lawfully

**Need**

As product owner, I need the system to detect drift in its own descriptive artifacts and recover without losing history.

**Given**

- A bootloader or self-description artifact derived from governing source truth
- A deterministic consistency check over that artifact
- A lawful recovery path

**When**

The bootloader drifts out of sync with the governing source.

**Then**

- The deterministic check fails and produces visible delta
- The artifact is corrected through the normal convergence path
- The event log explains both the drift and the recovery
- The system regains convergence without rewriting history

**Confirms**

- The system can govern its own descriptive layer
- Self-hosting drift is a first-class convergence problem
- Recovery remains event-sourced and lawful

---

## Scenario 21: A Derived Artifact Propagates Across Package Boundaries

**Need**

As product owner, I need one package to produce a derived artifact that another package can consume lawfully.

**Given**

- An upstream package that produces a derived artifact
- A downstream package that depends on that artifact as governing input
- Provenance linking the downstream use back to the upstream source

**When**

The upstream artifact changes and the downstream package re-evaluates.

**Then**

- The downstream package sees the new provenance surface explicitly
- Stale downstream convergence does not silently survive incompatible upstream changes
- The dependency is visible in events, projection, and delta
- Cross-package propagation is lawful rather than implicit file coupling

**Confirms**

- ABG can reason across package boundaries
- Derived artifacts can be consumed downstream without losing provenance
- The model scales beyond a single package as the unit of truth

---

## Scenario 22: Imported Graph-Function Libraries Compose Across Packages

**Need**

As product owner, I need reusable workflow libraries that can be imported and composed across package boundaries.

**Given**

- A library package exporting named graph functions
- A consuming package importing those functions
- Interface-compatible local workflows that can compose with the imported ones

**When**

The consuming package builds a larger workflow by composing imported and local graph functions.

**Then**

- Import boundaries preserve interface validation
- Versioned workflow structure is reusable across packages
- Composition remains lawful and explicit
- The resulting workflow is still replayable from package truth plus events

**Confirms**

- Graph-function libraries are real, not hypothetical
- Reuse scales from local structure to ecosystem structure
- GTL can support imported compositional assets without losing rigor

---

## Scenario 23: Distributed Saga Coordination Preserves Work Lineage

**Need**

As product owner, I need the system to coordinate distributed work across attempts, workers, and nodes without losing lineage or replayability.

**Given**

- One saga-like work lineage spanning multiple child work lines
- Multiple workers or nodes executing different parts of the lineage
- Compensation or correction required for one branch

**When**

Part of the distributed work fails, is retried, or is semantically compensated.

**Then**

- Work lineage remains the constitutional identity
- Attempt identity remains explicit and replayable
- Compensation is semantic correction, not destructive rollback
- Parent convergence reflects the lawful state of the distributed descendants
- The event stream remains sufficient to reconstruct the full distributed story

**Confirms**

- The local ABG model can scale into saga-style distribution
- Distribution does not require a different constitutional model
- Lineage, attempts, and compensation survive across nodes

---

## Why These 23

These 23 scenarios walk the product through the full ABG + GTL model:

1. Basic traversal
2. Deterministic failure
3. Escalation into construction
4. Human gate
5. Work identity
6. Provenance
7. Correction
8. Refinement
9. Recursion and fold-back
10. Run governance
11. Named functional workflows
12. Reusable workflow application
13. Workflow composition
14. Workflow selection by interface-compatible zoom
15. Higher-order gating
16. Fan-out over vectors
17. Fan-in reduction
18. End-to-end higher-order workflow
19. Governed leaf sub-work
20. Self-hosting drift and recovery
21. Cross-package propagation
22. Imported graph-function libraries
23. Distributed saga coordination

Together they form a much broader product-owner completeness pass for the system, including explicit passes over functional composition, higher-order workflow structure, self-governance, cross-package reuse, and distributed end-state coordination.

---

## Further Horizon

After these 23, the next most important additions are:

- Multi-worker orchestration over shared work lineages
- Cost / latency / quality arbitration between alternative workflow candidates
- Long-lived operational policies over retries, escalation, and compensation
- Formal laws and proofs for composition, gating, and replay
