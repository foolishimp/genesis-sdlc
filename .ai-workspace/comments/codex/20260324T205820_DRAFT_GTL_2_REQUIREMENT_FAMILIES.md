# GTL 2.x Requirement Families

**Status**: Draft
**Date**: 2026-03-24
**Purpose**: Derive a fresh requirement-family map from the constitutional intent of GTL 2.x, separating language law from ABG interpreter law.

---

## 1. Requirement Strategy

The fresh GTL 2.x requirement set should be split into two constitutions:

- **GTL language requirements**
- **ABG interpreter/runtime requirements**
- **engine-mapping requirements**

This avoids mixing:

- structural law
- runtime mechanics
- product policy

into one undifferentiated body.

The old mixed framing should not be carried forward.

---

## 2. GTL Language Requirement Families

These families follow directly from the constitutional intent and belong to GTL 2.x itself.

| Family ID | Family | Source intent | Scope |
| --- | --- | --- | --- |
| `REQ-L-GTL2-GRAPH` | Graph primacy and graph structure | `INT-GTL2-001` | Define `Graph` as the one structural type and specify its minimum structural obligations |
| `REQ-L-GTL2-NODE` | Typed nodes | `INT-GTL2-001` | Define `Node[T]` as the typed local locus of graph meaning |
| `REQ-L-GTL2-INTERFACE` | Interfaces and compatibility | `INT-GTL2-001`, `INT-GTL2-005`, `INT-GTL2-010` | Define interface declaration, interface satisfaction, and substitutability |
| `REQ-L-GTL2-OPERATOR` | Operator regimes and declarations | `INT-GTL2-003` | Define operator classes, regimes, bindings, and language-level operator semantics |
| `REQ-L-GTL2-RULE` | Rules and gates | `INT-GTL2-003`, `INT-GTL2-006` | Define rule declarations such as consensus, policy gates, and structural constraints |
| `REQ-L-GTL2-GRAPHFUNCTION` | Reusable named workflows | `INT-GTL2-004` | Define `GraphFunction`, interface obligations, and reuse semantics |
| `REQ-L-GTL2-VECTOR` | Primitive graph vectors | `INT-GTL2-001`, `INT-GTL2-005` | Define the minimal graph vector form currently approximated by `Edge` |
| `REQ-L-GTL2-COMPOSE` | Graph-function composition | `INT-GTL2-005` | Define lawful composition, composition validation, and composition laws |
| `REQ-L-GTL2-SUBSTITUTE` | Graph substitution/refinement | `INT-GTL2-005` | Define lawful substitution of a graph for a contract step while preserving the outer contract |
| `REQ-L-GTL2-RECURSE` | Recursive graph application | `INT-GTL2-006` | Define recursive graph semantics and recursive legality at the language level |
| `REQ-L-GTL2-HOF` | Higher-order graph operations | `INT-GTL2-006` | Define `fan_out`, `fan_in`, `gate`, and `promote` semantics |
| `REQ-L-GTL2-MODULE` | Module, import, and library structure | `INT-GTL2-004`, `INT-GTL2-011` | Define modules/packages, imports, graph-function libraries, and reuse surfaces |
| `REQ-L-GTL2-SELECTION-BOUNDARY` | Structural candidate exposure without strategic choice | `INT-GTL2-007` | Define what the language may expose for candidate visibility while forbidding embedded hidden selection |
| `REQ-L-GTL2-LAWS` | Language laws | `INT-GTL2-001`, `INT-GTL2-005`, `INT-GTL2-006`, `INT-GTL2-010` | State graph primacy, typed-node law, interface law, associativity, identity, substitutability, contract preservation, and replay suitability |
| `REQ-L-GTL2-ENGINE-INDEPENDENCE` | Engine-independent semantics | `INT-GTL2-009` | Define GTL semantics independently of any one runtime |

---

## 3. ABG Interpreter Requirement Families

These families are not GTL language law. They are the interpreter/runtime law for ABG as canonical interpreter.

| Family ID | Family | Source intent | Scope |
| --- | --- | --- | --- |
| `REQ-R-ABG2-INTERPRET` | Graph interpretation | `INT-GTL2-008`, `INT-GTL2-010` | Define how ABG materializes and interprets GTL graphs and graph functions |
| `REQ-R-ABG2-EVENTS` | Event model and emission | `INT-GTL2-008`, `INT-GTL2-010` | Define event classes needed to replay graph application truth |
| `REQ-R-ABG2-PROJECTION` | Projection and replay | `INT-GTL2-008`, `INT-GTL2-010` | Define replay/projection from event history into current truth |
| `REQ-R-ABG2-CONVERGENCE` | Delta and convergence | `INT-GTL2-008` | Define convergence as replayed truth over graph applications |
| `REQ-R-ABG2-LINEAGE` | Work lineage | `INT-GTL2-006`, `INT-GTL2-008` | Define lineage identity for graph application and recursive child application |
| `REQ-R-ABG2-RUN` | Run attempts and retry governance | `INT-GTL2-008` | Define execution attempts, failure handling, retries, and live-attempt semantics |
| `REQ-R-ABG2-CORRECTION` | Reset and correction | `INT-GTL2-008` | Define certification shadowing and post-boundary truth without mutating history |
| `REQ-R-ABG2-PROVENANCE` | Provenance binding | `INT-GTL2-008`, `INT-GTL2-010` | Define version/spec binding and carry-forward/invalidity behavior |
| `REQ-R-ABG2-SELECTION-APPLICATION` | Candidate enumeration, choice application, and provenance | `INT-GTL2-007`, `INT-GTL2-008` | Define interpreter-side candidate enumeration, external choice application, and replayable choice recording |
| `REQ-R-ABG2-SELFHOSTING` | Derived graph artifacts and self-description | `INT-GTL2-008` | Define interpreter/runtime treatment of bootloader and other derived graph artifacts |

---

## 4. Engine-Mapping Requirement Families

These families sit between pure language law and specific interpreter/runtime law.

They govern alternate engine mappings.

| Family ID | Family | Source intent | Scope |
| --- | --- | --- | --- |
| `REQ-M-GTL2-MAPPING` | Alternate engine mapping fidelity | `INT-GTL2-009`, `INT-GTL2-010` | Define how GTL semantics map onto engines other than ABG |
| `REQ-M-GTL2-CAPABILITY` | Capability profiles | `INT-GTL2-009` | Define how a target engine declares which GTL semantics it supports fully, partially, or not at all |
| `REQ-M-GTL2-PROVENANCE` | Mapping provenance | `INT-GTL2-009`, `INT-GTL2-010` | Define how alternate engines expose enough provenance to preserve semantic traceability |

---

## 5. Product-Layer Requirement Families

Some concerns should not be forced into either the GTL core or the ABG interpreter core.

These belong above them:

| Family ID | Family | Scope |
| --- | --- | --- |
| `REQ-P-POLICY` | Business and intent policy | Selection priorities, business routing, strategy, and product-level prioritization |
| `REQ-P-SCENARIOS` | Product scenario coverage | The concrete use cases the product must fulfill |
| `REQ-P-LIBRARIES` | Curated graph-function libraries | Domain-owned reusable workflow libraries and publication/import expectations |

This layer is where product meaning is preserved.

---

## 6. Recommended First Wave

If starting fresh, the first wave of constitutional requirements should be:

### GTL first wave

1. `REQ-L-GTL2-GRAPH`
2. `REQ-L-GTL2-NODE`
3. `REQ-L-GTL2-INTERFACE`
4. `REQ-L-GTL2-OPERATOR`
5. `REQ-L-GTL2-GRAPHFUNCTION`
6. `REQ-L-GTL2-COMPOSE`
7. `REQ-L-GTL2-SUBSTITUTE`
8. `REQ-L-GTL2-LAWS`

### ABG first wave

1. `REQ-R-ABG2-INTERPRET`
2. `REQ-R-ABG2-EVENTS`
3. `REQ-R-ABG2-PROJECTION`
4. `REQ-R-ABG2-CONVERGENCE`
5. `REQ-R-ABG2-LINEAGE`
6. `REQ-R-ABG2-SELECTION-APPLICATION`

This is enough to establish:

- graph-first language law
- interpreter separation
- composition/substitution
- evented replay

before pushing further into recursion, higher-order behavior, and self-hosting.

---

## 7. What to Re-mine From the Current Corpus

### Preserve as GTL language law

- typed structural topology
- typed node semantics
- operator classes
- graph reuse
- composition and substitution semantics
- workflow-library semantics

### Preserve as ABG interpreter law

- event calculus and projection
- delta/convergence
- work identity and run identity
- reset/correction
- provenance
- runtime governance

### Drop or rewrite

- duplicate structural terms for graph-shaped things
- command-shaped wording that belongs to the runtime rather than the language
- mixed constitutional wording that combines language law and runtime mechanics in one statement

---

## 8. Summary

The clean next constitution is not one large blended requirement stack.

It is:

- GTL language requirement families
- ABG interpreter requirement families
- engine-mapping requirement families
- product/policy/scenario requirement families above them

That separation follows directly from the new intent and should make the next requirement wave much cleaner than the old mixed model.
