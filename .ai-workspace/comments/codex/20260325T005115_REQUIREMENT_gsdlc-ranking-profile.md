# Requirement Note — GSDLC 2.1 Real-World GraphFunction Use Cases

**Status**: Draft review artifact
**Date**: 2026-03-25
**Purpose**: Capture four real-world GSDLC 2.1 use cases that must be preserved in the GTL 2.x wave:

- ranked decomposition with explicit delivery profiles
- gap-triggered schema discovery as a child graph feeding back into design
- review-gate consensus over an explicit artifact
- parallel worker harvest with explicit selection policy

---

## Use Case 1 — Ranked Decomposition with Explicit Delivery Profile

GSDLC shall support a reusable ranked-decomposition graph function whose materialization accepts an explicit delivery profile parameter:

- `steelthread`
- `optimal`
- `mvp`

This profile is a business/policy input to graph materialization.

It is not engine inference.

---

### Why This Matters

This is a real recurring use case:

- take an input asset
- decompose it
- tag the resulting work
- rank the delivery plan according to the desired delivery strategy

The workflow shape is reusable.

What varies is the ranking profile:

- `steelthread`: prioritize the thinnest end-to-end proving path
- `optimal`: prioritize the strongest or most complete solution ordering
- `mvp`: prioritize minimum viable delivery

So the correct model is:

- one graph function
- stable outer contract
- explicit profile parameter

not:

- hidden engine choice
- copied graphs per strategy
- implicit business logic in ABG

---

### GTL 2.x Shape

The intended GTL 2.x surface is:

```python
gsdlc_ranked_decomposition(
    asset,
    profile="steelthread" | "optimal" | "mvp",
)
```

Conceptually:

```text
asset
  -> decomposition
  -> tagged_decomposition
  -> ranked_delivery_plan
```

This should be expressed as:

- a named reusable `GraphFunction`
- parameterized materialization
- replayable selection/materialization provenance

---

### Constitutional Position

This requirement is consistent with the current GTL 2.x direction:

- GTL supports parameterized graph materialization
- selection/strategy remains outside hidden engine behavior
- ABG applies externally chosen structure and records provenance

The missing explicit rule to preserve is:

- materialization parameters such as `profile` must be replayable provenance

---

### Implications

1. GSDLC should expose ranked decomposition as a reusable library-grade graph function.
2. `steelthread | optimal | mvp` should be explicit materialization parameters, not separate ontological workflows unless their internals diverge substantially later.
3. ABG-compatible engines must not infer the profile.
4. Selection/materialization provenance should record the chosen profile.
5. Product scenarios should prove the same input asset can lawfully produce different ranked plans under different profiles.

---

## Use Case 2 — Gap-Triggered Schema Discovery Feeding Back Into Design

GSDLC shall support a child discovery graph that is triggered when a design flow detects a missing data schema.

The intended flow is:

```text
design
  -> schema_gap_detected
  -> discovery_intent
  -> graph.discovery(tool_profile="jupyternotebook", dataset)
  -> discovered_schema
  -> discovery_context_bundle
  -> design
```

This use case is not generic “discovery.”

It is specifically:

- a parent design flow detects missing schema truth
- the gap spawns discovery lineage
- discovery uses tool-capable F_P work over a dataset
- discovery produces a schema asset and reusable context bundle
- those outputs fold back into the parent design flow

### Why This Matters

This is a real design-time need:

- the design cannot proceed honestly because required schema truth does not yet exist
- the system must be able to leave the current path, discover the missing schema, and return with durable outputs

This pressures GTL 2.x in a useful way:

- recursive graph application
- tool-parameterized graph functions
- dataset-aware discovery
- output schema/context feeding back into parent design

### GTL 2.x Shape

The intended GTL 2.x surface is along the lines of:

```python
schema_discovery_from_gap(
    design,
    dataset,
    tool_profile="jupyternotebook",
)
```

Conceptually:

```text
design
  -> discovery_intent
  -> discovery_queries
  -> discovered_schema
  -> discovery_context_bundle
```

Where:

- `tool_profile="jupyternotebook"` is a materialization/operator parameter
- `dataset` is either a governed node or a bound context reference
- `discovered_schema` is a real output asset/node
- `discovery_context_bundle` is a reusable context output carried back into design

### Constitutional Position

This use case is consistent with the current GTL 2.x direction:

- GTL supports parameterized graph functions
- recursion/lineage is already constitutional
- ABG already owns lineage, replay, provenance, and fold-back
- tool execution belongs to operator realization, not hidden language structure

The explicit rule to preserve is:

- discovery materialization parameters and discovery outputs must be replayable provenance, not transient agent-only knowledge

### Implications

1. GSDLC should expose a reusable schema-discovery graph function.
2. Discovery should be spawnable from a detected design gap, not only from top-level intent.
3. The selected tool profile must remain explicit and replayable.
4. The discovered schema must be governed as a real output artifact.
5. Discovery-generated context must be reusable by the parent design flow.
6. Product scenarios should prove the parent graph can pause, spawn discovery, and continue with folded-back schema/context truth.

---

## Use Case 3 — Consensus-Gated Review Over an Explicit Artifact

GSDLC shall support a reusable review-gate graph function in which a presented artifact is reviewed by multiple judges and either accepted or returned with feedback until consensus is reached.

The intended flow is:

```text
artifact_document
  -> fan_out(worker_judge)
  -> judgments
  -> fan_in(consensus_result)
  -> gate(consensus_met)
  -> (accepted | feedback)
```

If feedback is returned:

```text
feedback_bundle
  -> revise artifact_document
  -> present again
```

This use case intentionally constrains review to the presented artifact.

The first lawful version should not give judges arbitrary ambient graph visibility.

### Why This Matters

This is a reusable review primitive for many GSDLC surfaces:

- testing QA review
- check-in / merge approvals
- intent changes
- requirement changes
- design approvals
- release/document gates

The judged artifact stays explicit.

That gives:

- cleaner replay
- cleaner provenance
- auditable disagreement
- less hidden context leakage

### GTL 2.x Shape

The intended GTL 2.x surface is along the lines of:

```python
review_gate(
    artifact_document,
    reviewers=...,
    consensus_policy=...,
)
```

Conceptually:

```text
artifact_document
  -> judgments
  -> consensus_decision
  -> (accepted_artifact | feedback_bundle)
```

Where:

- judges return `accepted` or `feedback`
- `consensus(...)` is rule + reducer/gate behavior
- accepted artifacts may be promoted into canonical state
- feedback loops back for revision

### Constitutional Position

This use case is consistent with the current GTL 2.x direction:

- higher-order fan-out/fan-in/gate already exist in the model
- evaluators and rules are already first-class
- recursion/feedback loops are already lawful
- promotion of accepted artifacts into governed state fits GTL 2.x

The explicit rule to preserve is:

- reviewers judge the presented artifact and explicit attached context only, not hidden ambient state, at least in the first constitutional version

### Implications

1. GSDLC should expose a reusable review-gate graph function.
2. Consensus policy must be explicit and replayable.
3. Judge outputs should be constrained to accepted/feedback-style judgments with durable provenance.
4. Feedback loops should remain lawful recursive graph application.
5. Product scenarios should prove the same review function can serve QA, check-in approval, and intent/requirement/design review gates.

---

## Use Case 4 — Parallel Worker Harvest with Explicit Selection Policy

GSDLC shall support a reusable parallel-harvest graph function in which multiple workers produce candidate outputs in parallel and the system harvests them under an explicit strategy.

The intended flow is:

```text
artifact_or_problem
  -> fan_out(worker_build)
  -> candidate_outputs
  -> fan_in(harvest_policy)
  -> selected_or_merged_output
```

Representative harvest policies include:

- `winner_take_all`
- `cherry_pick`
- `runoff`
- `ensemble`
- `best_score`
- `consensus_merge`

### Why This Matters

This is the sibling reusable pattern to review-gate:

- instead of many judges over one artifact
- many workers produce candidate artifacts
- one explicit policy governs harvest

It supports:

- competing designs
- alternative implementations
- parallel coding
- bake-offs between strategies
- merge/cherry-pick style synthesis

### GTL 2.x Shape

The intended GTL 2.x surface is along the lines of:

```python
parallel_harvest(
    artifact_or_problem,
    workers=...,
    harvest_policy="winner_take_all" | "cherry_pick" | "runoff" | ...,
)
```

Conceptually:

```text
artifact_or_problem
  -> candidate_outputs
  -> harvest_decision
  -> final_output
```

Where:

- the worker set is explicit
- the harvest policy is explicit
- the winning/merged output becomes the governed artifact

### Constitutional Position

This use case is consistent with the current GTL 2.x direction:

- fan-out/fan-in are already first-class higher-order operations
- selection must remain explicit, not hidden engine behavior
- ABG already owns provenance, lineage, replay, and evented application

The explicit rule to preserve is:

- harvest policy must be externalized and replayable provenance, not an implicit engine heuristic

### Implications

1. GSDLC should expose a reusable parallel-harvest graph function.
2. Harvest policy must be explicit and durable in provenance.
3. Worker participation and candidate outputs must be replayable.
4. Product scenarios should prove multiple harvest policies over the same input/worker set.
5. This should become a standard library-grade GSDLC higher-order workflow primitive alongside review-gate.

---

## Suggested Follow-on

These should become:

- GSDLC product scenarios
- GTL 2.x requirement or requirement extensions around parameterized graph materialization provenance
- early library graph functions once the GTL 2.x migration begins

---

## Bottom Line

Do not lose these:

1. **GSDLC needs a reusable ranked-decomposition graph function with explicit delivery-ranking profile parameters (`steelthread`, `optimal`, `mvp`), and the chosen profile must remain external to engine choice and visible in provenance.**
2. **GSDLC also needs a gap-triggered schema-discovery child graph that can use tool-capable discovery over a dataset, produce a governed schema asset plus reusable context, and fold those outputs back into design.**
3. **GSDLC needs a reusable consensus-gated review function over an explicit artifact, with accepted/feedback judgments and lawful recursive revision until consensus is reached.**
4. **GSDLC needs a reusable parallel-harvest function where multiple workers produce candidate outputs and an explicit harvest policy selects or merges the final governed artifact.**
