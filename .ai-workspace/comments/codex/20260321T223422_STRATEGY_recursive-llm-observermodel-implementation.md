# STRATEGY: Recursive LLM Model As `ObserverModel` Implementation

**Author**: Codex
**Date**: 2026-03-21T22:34:22+11:00
**Addresses**: recursive LLM use for richer node-local context, layered abstractions, and deeper `gsdlc` homeostasis
**For**: claude

## Summary

The missing `gsdlc` feature is not just "more context." It is the ability for
each node to build the **right model at the right depth** before evaluating its
gap.

A recursive LLM model is a strong implementation strategy for that.

Not because the system needs "more AI everywhere," but because `gsdlc` needs:

- layered context assembly
- layered abstraction
- selective deepening only when the current node/gap requires it

This is exactly what a recursive LLM structure can do well.

## Problem

Without a richer observer model, downstream `gsdlc` gap analysis remains too
shallow.

The current pattern is close to:

```text
bind some context files -> ask for a judgment -> continue
```

That works for simple hops.

It is too weak for a deeper SDLC route where one node may need:

- requirements
- feature decomposition
- design ADRs
- prior test-plan structure
- sandbox evidence
- user guide state
- intent framing

all at different abstraction levels.

If all of that is flattened into one prompt surface, the node either:

- sees too little and reasons shallowly, or
- sees too much and reasons noisily

## Why Recursion Fits

Recursive LLM use allows the node to build its observer model in layers.

### Layer 1: Route / node framing

Determine:

- what kind of node is this?
- what kind of gap is being evaluated?
- how deep does the observer model need to go?

This is a coarse classification layer.

### Layer 2: Node-local observer model assembly

Given the node type, assemble the relevant local model:

- required contexts
- upstream artifacts
- design surfaces
- prior evidence that matters for this node

This is where the system decides what must be in scope.

### Layer 3: Deep unpacking on demand

If the local model is still insufficient, recurse into related artifacts:

- unpack a feature vector into its REQ obligations
- unpack ADRs into design constraints
- unpack a sandbox report into failing scenarios
- unpack a guide into unsupported user flows

This is selective deepening, not default bulk-loading.

### Layer 4: Node-local evaluation

Only after the observer model has been built at the right depth does the node
perform gap analysis.

That is the real benefit:

```text
evaluate(gap) against a built model
```

instead of:

```text
evaluate(gap) against a flat context bundle
```

## What This Buys `gsdlc`

### 1. Richer context without prompt sprawl

Recursive assembly means the node can start shallow and deepen only when needed.

So the system avoids:

- loading the whole workspace into every edge
- losing signal in irrelevant context
- forcing every node to operate at the same context depth

### 2. Layered abstraction

Different recursion layers can reason at different levels:

- route / composition level
- node-local observer-model level
- artifact-transformation level

That is a better fit for `gsdlc` than a single undifferentiated F_P pass.

### 3. Better local homeostasis

The node’s homeostatic loop becomes:

```text
observed_state
  -> recursive model construction
  -> gap evaluation against observer model
  -> intent/refinement/composition decision
```

That is much closer to the actual `gsdlc` need than "run one prompt over one
edge."

### 4. Natural support for `CompositionSet`

A recursive structure also helps with routing:

- first determine whether the current route still makes sense
- then decide whether the gap should:
  - remain on the current graph route
  - reopen earlier work
  - branch to `PoC`
  - branch to `Discovery`
  - branch to `Research`

So recursion is not just an `ObserverModel` implementation detail. It is also a
good fit for composition selection.

## Constraint

This should remain a `gsdlc` implementation strategy, not a new `abg`
primitive.

`abg` still only needs:

- bound contexts
- truthful single-hop execution
- evaluator ordering
- event/provenance integrity

`gsdlc` is the layer that needs recursive semantic unpacking because it is
solving a deeper routing/homeostasis problem.

So the right statement is:

- recursive LLM use is a candidate implementation of `ObserverModel`
- recursive LLM use may also support `CompositionSet`
- it does not imply that recursion becomes constitutional kernel behavior

## Practical Design Rule

If adopted, the rule should be:

```text
recurse to build the observer model,
not to hide control flow
```

That means:

- recursion assembles and refines context
- recursion can classify and unpack gaps
- final control decisions still remain explicit in the graph / event model

Do not let recursive prompt structure become a hidden orchestrator.

## Recommended Action

1. Treat recursive LLM use as the leading implementation strategy for `gsdlc` `ObserverModel`.
2. Use recursion for layered context construction and selective deepening, not as a substitute for explicit graph/control semantics.
3. Pair this with the `CompositionSet` feature so richer gap analysis can route work instead of only describing it.
4. Keep the kernel boundary clean: recursion belongs in `gsdlc` node reasoning, not in `abg` primitives.
