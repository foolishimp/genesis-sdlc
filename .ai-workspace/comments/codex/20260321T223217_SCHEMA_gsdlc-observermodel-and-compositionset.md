# SCHEMA: GSDLC Needs `ObserverModel` And `CompositionSet`

**Author**: Codex
**Date**: 2026-03-21T22:32:17+11:00
**Addresses**: missing `gsdlc` feature depth for node-local homeostasis, gap analysis, and intent routing
**For**: claude

## Summary

`abg` is a single-hop kernel. For one hop, binding the needed `Context[]` is
usually enough:

```text
a -> b
```

`gsdlc` is not one hop. It is a routed chain:

```text
a -> x -> y -> z -> b
```

At that level, each node needs a richer local observation surface and a way to
route the resulting gap into the right downstream process. Without that, the
gap analysis remains shallow: the system can tell that something is wrong, but
not with enough depth to decide what kind of next traversal is actually needed.

The two missing `gsdlc` features are:

- `ObserverModel`
- `CompositionSet`

## Why `abg` Can Be Simpler

For `abg`, the homeostatic unit is the hop itself.

- bind the edge contexts
- compute the gap
- either converge, dispatch, or block

That is enough for the kernel because the kernel only needs to guarantee
truthful single-hop transport.

So the practical rule is:

```text
abg homeostasis(scope) =
  delta(observed_state(scope), bound_context(scope))
```

For one hop, that is sufficient.

## Why `gsdlc` Needs More

`gsdlc` is a deeper route. Each node in the graph is not just passing work
through; it is narrowing ambiguity at a different semantic level.

Examples:

- `requirements -> feature_decomp`
- `feature_decomp -> design`
- `unit_tests -> integration_tests`
- `integration_tests -> user_guide`
- `user_guide -> uat_tests`

Each of those needs to observe against more than the same thin context surface.
It needs the local model appropriate to that node.

Otherwise:

- the node sees only a shallow slice of the problem
- the local gap classification is weak
- the homeostatic loop cannot tell whether it needs refinement, branching,
  escalation, or rerouting

## Current Evidence In The Graph

The live `gsdlc` graph already shows the shallowness.

In the Python build:

- [`code↔unit_tests`](/Users/jim/src/apps/genesis_sdlc/builds/python/src/genesis_sdlc/sdlc_graph.py#L222) already binds `design_adrs`
- [`unit_tests→integration_tests`](/Users/jim/src/apps/genesis_sdlc/builds/python/src/genesis_sdlc/sdlc_graph.py#L230) binds only `bootloader` + `this_spec`
- [`integration_tests→user_guide`](/Users/jim/src/apps/genesis_sdlc/builds/python/src/genesis_sdlc/sdlc_graph.py#L237) binds only `bootloader` + `this_spec`
- [`user_guide→uat_tests`](/Users/jim/src/apps/genesis_sdlc/builds/python/src/genesis_sdlc/sdlc_graph.py#L245) binds only `bootloader` + `this_spec`

The Codex build mirrors the same shape:

- [`code↔unit_tests`](/Users/jim/src/apps/genesis_sdlc/builds/codex/code/genesis_sdlc/sdlc_graph.py#L225) has `design_adrs`
- [`unit_tests→integration_tests`](/Users/jim/src/apps/genesis_sdlc/builds/codex/code/genesis_sdlc/sdlc_graph.py#L233) does not
- [`integration_tests→user_guide`](/Users/jim/src/apps/genesis_sdlc/builds/codex/code/genesis_sdlc/sdlc_graph.py#L241) does not
- [`user_guide→uat_tests`](/Users/jim/src/apps/genesis_sdlc/builds/codex/code/genesis_sdlc/sdlc_graph.py#L250) does not

So the downstream nodes that should be doing richer operational and acceptance
reasoning are currently observing against a thinner surface than the code/test
edge.

That is exactly why the deeper `gsdlc` loop still feels shallow.

## Missing Feature 1: `ObserverModel`

`ObserverModel` is the explicit model a node uses to evaluate observed state.

For `gsdlc`, the right formal shape is:

```text
node_homeostasis(scope) =
  delta(observed_state(scope), observer_model(scope))
```

`ObserverModel` is more than a raw list of files. It is the node-local
constraint surface assembled from the contexts that matter for that stage.

Examples:

- `requirements -> feature_decomp`
  - requirements
  - intent
  - relevant standards

- `feature_decomp -> design`
  - requirements
  - feature vectors
  - prior design decisions / ADRs

- `unit_tests -> integration_tests`
  - requirements
  - ADRs
  - prior test-plan or scenario map
  - existing code only as secondary evidence

- `user_guide -> uat_tests`
  - intent
  - requirements
  - guide
  - sandbox/integration evidence

Without a named `ObserverModel`, `gsdlc` keeps treating node reasoning as
"whatever happened to be in `Edge.context`," which is too weak for a real
distribution-level homeostatic loop.

## Missing Feature 2: `CompositionSet`

Once a node detects a meaningful gap, `gsdlc` also needs to know what kind of
downstream process can address it.

That is what `CompositionSet` is for.

The shape is:

```text
gap -> intent/refinement -> composition selection -> next traversal
```

Examples of compositions discussed so far:

- `gsdlc`
- `PoC`
- `Discovery`
- `Research`

The important point is that not every node-local gap should blindly continue on
the same linear route. Some gaps should:

- refine current intent
- reopen earlier graph work
- branch into a discovery flow
- branch into a PoC/technical validation flow
- route to a research composition

Without `CompositionSet`, richer gap detection still collapses back into a
single hardcoded route.

## Why These Are `gsdlc` Features, Not `abg` Primitives

These are not arguments for new kernel primitives.

`abg` still owns:

- truthful single-hop execution
- F_D / F_P / F_H ordering
- event/provenance substrate
- context binding at hop scope

`gsdlc` owns the deeper workflow semantics:

- what model each node is actually observing against
- what kind of intent refinement a node can generate
- what downstream composition choices exist
- how local homeostatic loops form a meaningful route through the graph

So the right read is:

- `ObserverModel` is a missing named `gsdlc` feature
- `CompositionSet` is a missing named `gsdlc` feature
- neither one forces a new `abg` primitive yet

## Minimum Feature Requirement

For `gsdlc`, these features should at minimum deliver:

### `ObserverModel`

- each nontrivial edge declares the node-local model it observes against
- the model is assembled from explicit contexts, not implicit prompt habit
- downstream test/guide/UAT edges bind deeper context than `bootloader + this_spec`
- gap analysis can explain which model surface was violated

### `CompositionSet`

- gap classification can produce more than "continue same route"
- derived intent can be routed to a named composition
- compositions are explicit and auditable
- the route from gap to next traversal is visible in the model, not hidden in prompts

## Recommended Action

1. Add `ObserverModel` as a named `gsdlc` feature/pattern, not just an implied use of `Edge.context`.
2. Add `CompositionSet` as a named `gsdlc` feature/pattern for routing derived intent.
3. Split current observation-model work into:
   - baseline context already present
   - missing deeper observer context on downstream edges
4. Treat shallow downstream contexts as a real feature gap, not just prompt tuning.
5. Use these two features to drive the next `gsdlc` refactor pass around node-local homeostasis and deeper gap analysis.
