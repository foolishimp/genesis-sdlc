# GTL 2.x -> ABG Contract and GTL 1.0 Disposition

**Status**: Draft
**Date**: 2026-03-24
**Purpose**: Define the forward GTL 2.x target-engine contract and the backward disposition of the visible GTL/ABG 1.0 requirement corpus so no prior law remains accidental.

This document is the migration control plane that sits beside:

- [20260324T213129_MASTER_GTL_2_CONSTITUTIONAL_DESIGN.md](/Users/jim/src/apps/genesis_sdlc/.ai-workspace/comments/codex/20260324T213129_MASTER_GTL_2_CONSTITUTIONAL_DESIGN.md)

The master document defines the target language and engine-boundary model.

This document defines:

- what the canonical ABG target engine surface must do for GTL 2.x
- what the current GTL/ABG 1.0 requirement families become
- how the migration will be phased without silent inherited law

---

## 1. Position

There are two obligations in the GTL 2.x wave:

1. **Forward contract**
   Define the canonical engine surface GTL 2.x requires.

2. **Backward disposition**
   Classify every inherited GTL/ABG 1.0 requirement as:
   - replaced
   - subsumed
   - retired

Nothing leaves unclassified.

This follows the same method already used elsewhere:

- every new constitutional surface must have an explicit contract
- every inherited law must have an explicit fate

---

## 2. Source Set

This first pass is grounded against the visible GTL/ABG 1.0 requirement files under:

- `/Users/jim/src/apps/abiogenesis/specification/requirements`

Visible requirement-family files:

- `REQ-F-BOOT`
- `REQ-F-BOOTDOC`
- `REQ-F-CMD`
- `REQ-F-COMP`
- `REQ-F-CORE`
- `REQ-F-CORRECT`
- `REQ-F-DOCS`
- `REQ-F-EC`
- `REQ-F-EVAL`
- `REQ-F-FRAG`
- `REQ-F-GATE`
- `REQ-F-GRAPH`
- `REQ-F-LEAF`
- `REQ-F-PROV`
- `REQ-F-REFINE`
- `REQ-F-RUN`
- `REQ-F-TAG`
- `REQ-F-TEST`
- `REQ-F-TRAV`
- `REQ-F-VIS`
- `REQ-F-WK`
- `REQ-F-WKSP`

No `REQ-NF-*` files are visible in that folder at this time.

This document therefore operates in two passes:

- **family-level classification now**
- **per-requirement-key classification next**

The final exhaustive migration still has to happen at individual requirement-key granularity.

---

## 3. Classification Rules

### Replaced by 2.0

A GTL 2.x, ABG 2.x, mapping, or product-layer requirement explicitly supersedes the 1.0 requirement.

Use this when:

- the concern survives
- but its formulation, ontology, or layer placement changes materially

### Subsumed

The 1.0 requirement becomes a degenerate or narrower case of a broader 2.0 requirement.

Use this when:

- the concern survives substantially intact
- and the 2.0 law strictly contains it

### Retired

The 1.0 requirement no longer belongs to the intended constitutional system.

Use this when:

- the concept was transitional/bootstrap vocabulary
- the concern belongs only to a local implementation convenience
- or the concern moves out of constitutional law entirely

### Family-level provisional note

Classification is ultimately per requirement key.

At family level, some files are only **provisionally** repriced because different keys inside the family may split across:

- GTL language law
- ABG target-engine law
- engine-mapping law
- product/policy law
- retirement

When that happens, the family-level row states the dominant posture and the note records the required split.

---

## 4. Forward Contract: GTL -> ABG Target Engine Surface

GTL 2.x is engine-agnostic.

ABG is the **canonical target engine surface** for GTL:

- not a single implementation
- not identical to the current local/workspace codebase
- not the only possible runtime mapping

Multiple ABG-compatible implementations may exist:

- local/workspace-first
- distributed/cloud-first
- queue-driven
- service-oriented

They remain ABG-compatible as long as they preserve the same engine contract.

The contract is about interpreter obligations, not implementation topology.

---

## 5. GTL -> ABG Capability Contract

| Capability ID | Capability | GTL 2.x driver | Current ABG state | ABG 2.x contract obligation | Phase |
| --- | --- | --- | --- | --- | --- |
| `ABG-CAP-001` | Load structural declarations | `Graph`, `Node[T]`, `Operator`, `Evaluator`, `Rule`, `GraphFunction`, `Module` | `partial` | Load GTL 2.x structural declarations without collapsing them into GTL 1.0 shapes | A |
| `ABG-CAP-002` | Interpret primitive graph vectors | Edge-as-minimal-graph law | `strong-ish` | Treat primitive step traversal as interpretation of minimal graphs, not a rival ontology | A |
| `ABG-CAP-003` | Materialize graph templates | `GraphFunction` and layered graph model | `weak` | Materialize graphs from declared templates and parameters, including cardinality-sensitive materialization where lawful | B |
| `ABG-CAP-004` | Execute operator bindings | First-class operator regimes | `strong` | Execute deterministic, probabilistic, and human operator bindings | A |
| `ABG-CAP-005` | Execute evaluator bindings | First-class evaluator declarations | `strong` | Execute plugin-bound evaluator bindings and record evaluation attempts/results/provenance | A |
| `ABG-CAP-006` | Enumerate lawful candidates | Selection boundary | `partial` | Enumerate compatible graph or graph-function candidates without strategic choice | B |
| `ABG-CAP-007` | Apply externally chosen workflow | Selection boundary | `partial` | Accept external choice, apply it lawfully, and record provenance of selection | B |
| `ABG-CAP-008` | Apply graph substitution | Substitute/refine law | `partial` | Replace coarse graph contracts with compatible inner graphs while preserving outer contract | B |
| `ABG-CAP-009` | Interpret composition | Compose law | `missing` | Interpret composed graph functions lawfully and replayably | C |
| `ABG-CAP-010` | Preserve layered graph separation | Layered graph model | `implicit` | Distinguish topology, materialized, execution, lineage, and composition layers in runtime interpretation | B |
| `ABG-CAP-011` | Preserve lineage | Recursive and work-lineage law | `good` | Preserve work identity and parent/child lineage across graph applications | A |
| `ABG-CAP-012` | Govern run attempts | Run governance | `partial` | Model attempts, retries, timeouts, supersession, and live-attempt semantics over graph executions | B |
| `ABG-CAP-013` | Replay truth | Event-sourced suitability | `good` | Reconstruct current truth from graph-application history | A |
| `ABG-CAP-014` | Compute convergence | Evaluator and convergence law | `good` | Compute convergence over graph application history rather than ad hoc command logic | A |
| `ABG-CAP-015` | Apply correction/reset | Correction law | `good/partial` | Shadow certifications and preserve truthful history across graph applications | B |
| `ABG-CAP-016` | Bind provenance | Provenance law | `good` | Preserve spec/workflow/version/selection provenance over graph interpretation | A |
| `ABG-CAP-017` | Realize bounded sub-work | GTL bounded sub-work capability | `partial` | Realize GTL-declared bounded sub-work through `LeafTask` or equivalent runtime construct | C |
| `ABG-CAP-018` | Realize higher-order graph ops | `fan_out`, `fan_in`, `gate`, `promote` | `missing` | Interpret higher-order graph operations as lawful runtime behavior | D |
| `ABG-CAP-019` | Govern derived graph artifacts | Self-hosting and bootloader surfaces | `partial/good` | Govern derived artifacts and self-description under the same replay/provenance discipline | C |
| `ABG-CAP-020` | Expose ABG-compatible contract | Engine-independence and mapping law | `missing` | Publish a stable contract that alternate implementations can satisfy | B |

---

## 6. Capability Phases

### Phase A: Interpreter viability

Minimum contract for Wave 1 GTL 2.x:

- `ABG-CAP-001`
- `ABG-CAP-002`
- `ABG-CAP-004`
- `ABG-CAP-005`
- `ABG-CAP-011`
- `ABG-CAP-013`
- `ABG-CAP-014`
- `ABG-CAP-016`

This is enough to say:

- ABG is viable as the canonical target engine surface for the first GTL 2.x requirement wave

### Phase B: True GTL 2.x alignment

- `ABG-CAP-003`
- `ABG-CAP-006`
- `ABG-CAP-007`
- `ABG-CAP-008`
- `ABG-CAP-010`
- `ABG-CAP-012`
- `ABG-CAP-015`
- `ABG-CAP-020`

This is enough to say:

- ABG interprets GTL 2.x directly rather than only a GTL 1.0 projection

### Phase C: Advanced runtime realization

- `ABG-CAP-009`
- `ABG-CAP-017`
- `ABG-CAP-019`

### Phase D: Higher-order realization

- `ABG-CAP-018`

---

## 7. Current Baseline Summary

Current GTL/ABG is already strong enough in:

- embedded Python DSL form
- operator execution
- evaluator execution
- event/replay spine
- convergence/delta foundations
- lineage/provenance foundations

Current GTL/ABG is still weak or missing in:

- graph-first structural center
- typed-node authoring surface
- graph-function materialization as a first-class concept
- graph-first substitution and composition
- higher-order graph interpretation
- explicit ABG-compatible surface contract

So the migration is not from zero.

It is from a **partial projection** to a **fuller algebra**.

---

## 8. Backward Disposition Scope

The backward map must eliminate silent inherited law from:

- GTL 1.0 language-shaped requirements
- ABG 1.0 runtime-shaped requirements
- local implementation/bootstrap requirements that still implicitly govern the current system

The rule is:

- nothing remains live merely because it once existed

---

## 9. Family-Level First Pass

This section classifies the visible GTL/ABG 1.0 requirement files at family granularity.

It is not the final per-key pass, but it is concrete enough to guide the next wave.

| 1.0 family | Provisional classification | 2.0 target | Notes |
| --- | --- | --- | --- |
| `REQ-F-BOOT` | `replaced` | `REQ-M-GTL2-MAPPING`, `REQ-P-POLICY`, possibly local ABG implementation requirements | `.genesis/` bootstrapping and starter-spec generation are local implementation/bootstrap concerns, not GTL language law |
| `REQ-F-BOOTDOC` | `subsumed` | `REQ-R-ABG2-SELFHOSTING`, `REQ-R-ABG2-PROVENANCE`, `REQ-P-SCENARIOS` | Derived artifact governance survives; wording must move from "graph asset in Package" to graph-first self-hosting law |
| `REQ-F-CMD` | `replaced` | `REQ-R-ABG2-INTERPRET`, `REQ-R-ABG2-CONVERGENCE`, local CLI/product requirements | Command names and CLI loops are not GTL language law; interpreter obligations survive, CLI specifics should be repriced separately |
| `REQ-F-COMP` | `replaced` | `REQ-L-GTL2-GRAPHFUNCTION`, `REQ-L-GTL2-COMPOSE`, `REQ-L-GTL2-MODULE` | The capability survives, but "Fragment produces Fragment" wording is replaced by graph-first graph-function law |
| `REQ-F-CORE` | `replaced` | `REQ-R-ABG2-INTERPRET`, `REQ-R-ABG2-EVENTS`, `REQ-R-ABG2-PROJECTION` | Engine-correctness concerns survive, but they belong to the target engine surface, not GTL ontology |
| `REQ-F-CORRECT` | `subsumed` | `REQ-R-ABG2-CORRECTION` | Correction/reset remains core interpreter law |
| `REQ-F-DOCS` | `retired` | product documentation backlog, not constitutional GTL/ABG law | Documentation remains necessary, but it should not govern the language/interpreter constitution |
| `REQ-F-EC` | `replaced` | `REQ-R-ABG2-EVENTS`, `REQ-R-ABG2-PROJECTION`, `REQ-R-ABG2-CONVERGENCE` | Event-sourced runtime survives; the exact 1.0 event-calculus phrasing must be repriced under the GTL 2.x / ABG 2.x split |
| `REQ-F-EVAL` | `replaced` | `REQ-L-GTL2-EVALUATOR`, `REQ-R-ABG2-CONVERGENCE`, `REQ-R-ABG2-PROVENANCE` | Evaluator survives as first-class GTL declaration with plugin-dependent realization and engine-owned evaluation instances |
| `REQ-F-FRAG` | `replaced` | `REQ-L-GTL2-GRAPH`, `REQ-L-GTL2-SUBSTITUTE`, `REQ-L-GTL2-COMPOSE` | The capability survives; the fragment ontology is retired in favor of graph-only structure |
| `REQ-F-GATE` | `subsumed` | `REQ-L-GTL2-RULE`, `REQ-L-GTL2-EVALUATOR`, `REQ-R-ABG2-CONVERGENCE` | Human gates survive as evaluator/rule/interpreter behavior |
| `REQ-F-GRAPH` | `replaced` | `REQ-L-GTL2-GRAPH`, `REQ-L-GTL2-NODE`, `REQ-L-GTL2-INTERFACE`, `REQ-L-GTL2-MODULE` | The graph-defining role survives, but Package/Asset/Edge wording is replaced by Graph/Node[T]/Module law |
| `REQ-F-LEAF` | `subsumed` | `REQ-L-GTL2-SUBWORK`, `REQ-R-ABG2-LEAFTASK`, `REQ-R-ABG2-RUN` | Bounded sub-work survives; GTL declares capability, ABG realizes it operationally |
| `REQ-F-PROV` | `subsumed` | `REQ-R-ABG2-PROVENANCE` | Provenance survives directly as target-engine law |
| `REQ-F-REFINE` | `replaced` | `REQ-L-GTL2-SUBSTITUTE`, `REQ-L-GTL2-RECURSE`, `REQ-R-ABG2-LINEAGE`, `REQ-R-ABG2-PROVENANCE` | Automatic refinement provenance survives, but now through graph substitution and lineage rather than fragment vocabulary |
| `REQ-F-RUN` | `subsumed` | `REQ-R-ABG2-RUN` | Run governance remains interpreter law |
| `REQ-F-TAG` | `retired` | methodology/tooling, not GTL/ABG constitutional law | Traceability still matters, but as method/tooling law rather than GTL or ABG semantics |
| `REQ-F-TEST` | `retired` | methodology/QA discipline | Test architecture should live in methodology and product QA, not in the GTL/ABG constitutional stack |
| `REQ-F-TRAV` | `subsumed` | `REQ-R-ABG2-INTERPRET`, `REQ-R-ABG2-CONVERGENCE`, `REQ-R-ABG2-LINEAGE` | Traversal law survives as graph interpretation law at the engine surface |
| `REQ-F-VIS` | `replaced` | `REQ-P-SCENARIOS`, local product/runtime requirements | Feature-closing behavior is product/runtime policy above the core GTL language |
| `REQ-F-WK` | `subsumed` | `REQ-R-ABG2-LINEAGE` | Work identity survives directly as lineage/interpreter law |
| `REQ-F-WKSP` | `replaced` | `REQ-R-ABG2-EVENTS`, local ABG implementation requirements | Event-stream binding survives; workspace path/bootstrap specifics are implementation-local |

---

## 10. Key Family Splits To Expect In The Per-Key Pass

Some 1.0 families are visibly mixed and will need key-level splitting.

### `REQ-F-BOOT`

Expected split:

- local bootstrap/install behavior -> local ABG implementation requirements or retirement
- starter-spec scaffolding -> GTL module/package scaffolding or product tooling

### `REQ-F-CMD`

Expected split:

- convergence/reporting/interpreter semantics -> `REQ-R-ABG2-*`
- CLI command naming and loop behavior -> product or implementation-local requirements

### `REQ-F-EC`

Expected split:

- evented replay/projection/convergence -> `REQ-R-ABG2-*`
- 1.0-specific event taxonomy details -> repriced or retired where they were overly shaped by the old kernel

### `REQ-F-EVAL`

Expected split:

- evaluator declaration semantics -> `REQ-L-GTL2-EVALUATOR`
- evaluation execution/provenance -> `REQ-R-ABG2-*`

### `REQ-F-GRAPH`

Expected split:

- structural graph law -> `REQ-L-GTL2-GRAPH`
- typed local loci -> `REQ-L-GTL2-NODE`
- old Package/Asset/Edge wording -> replaced

### `REQ-F-WKSP`

Expected split:

- generic event-stream binding requirement -> `REQ-R-ABG2-EVENTS`
- local filesystem workspace bootstrapping -> implementation-local

---

## 11. Immediate 2.0 Requirement Targets

The first 2.0 families that need to exist in constitutional text for the migration to proceed cleanly are:

### GTL language

- `REQ-L-GTL2-GRAPH`
- `REQ-L-GTL2-NODE`
- `REQ-L-GTL2-INTERFACE`
- `REQ-L-GTL2-OPERATOR`
- `REQ-L-GTL2-EVALUATOR`
- `REQ-L-GTL2-RULE`
- `REQ-L-GTL2-GRAPHFUNCTION`
- `REQ-L-GTL2-COMPOSE`
- `REQ-L-GTL2-SUBSTITUTE`
- `REQ-L-GTL2-RECURSE`
- `REQ-L-GTL2-MODULE`
- `REQ-L-GTL2-SUBWORK`

### ABG target engine surface

- `REQ-R-ABG2-INTERPRET`
- `REQ-R-ABG2-EVENTS`
- `REQ-R-ABG2-PROJECTION`
- `REQ-R-ABG2-CONVERGENCE`
- `REQ-R-ABG2-LINEAGE`
- `REQ-R-ABG2-RUN`
- `REQ-R-ABG2-CORRECTION`
- `REQ-R-ABG2-PROVENANCE`
- `REQ-R-ABG2-SELECTION-APPLICATION`
- `REQ-R-ABG2-LEAFTASK`
- `REQ-R-ABG2-SELFHOSTING`

### Engine mapping and product

- `REQ-M-GTL2-MAPPING`
- `REQ-M-GTL2-CAPABILITY`
- `REQ-M-GTL2-PROVENANCE`
- `REQ-P-POLICY`
- `REQ-P-SCENARIOS`
- `REQ-P-LIBRARIES`

---

## 12. Recommended Working Order

1. Freeze the master GTL 2.x design as the target model.
2. Freeze this document as the migration control plane.
3. Write the first wave of GTL 2.x language requirements.
4. Write the first wave of ABG target-engine requirements.
5. Perform the full per-key 1.0 classification pass.
6. Only then declare any 1.0 area non-governing.

---

## 13. Exit Criteria

The GTL 2.x migration control plane is complete only when:

- every visible 1.0 requirement key is classified as replaced, subsumed, or retired
- every GTL -> ABG capability has an owning 2.0 requirement family
- every retained 1.0 concern has a 2.0 home
- local implementation conveniences are explicitly separated from constitutional law
- no prior requirement remains live merely because nobody classified it

---

## 14. Bottom Line

This document defines the two controls needed to transform the system without accidental law:

1. **Forward contract**
   What GTL 2.x requires from the ABG target engine surface.

2. **Backward disposition**
   What the GTL/ABG 1.0 requirement corpus becomes.

The next wave should not start from implementation.

It should start from:

- the GTL 2.x target model
- the GTL -> ABG engine contract
- the explicit disposition of inherited law

That is how GTL 2.x replaces GTL 1.0 constitutionally rather than merely informally.
