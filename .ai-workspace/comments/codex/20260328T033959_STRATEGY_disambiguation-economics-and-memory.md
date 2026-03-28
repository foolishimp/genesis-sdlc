# STRATEGY: Disambiguation Economics And Memory

**Author**: codex
**Date**: 2026-03-28T03:40:08+1100
**Addresses**: methodology tradeoff between narrow pre-configuration, broad ambiguous transformation, and process memory
**Status**: Draft

## Summary

There is a real economic tradeoff between pre-configured precision and runtime ambiguity.

A narrow system spends more energy up front to reduce ambiguity before execution. That makes each later transformation cheaper, faster, and more reusable inside a bounded problem class. The cost is reduced generality. A broad system carries less upfront structure, so each transformation must spend energy disambiguating intent, context, and local meaning at runtime. That increases per-run cost, but preserves reach across a wider problem space.

The right methodological move is not to choose one side absolutely. It is to support both modes and to add memory that captures prior disambiguations so the same ambiguity does not need to be paid for repeatedly. This is not model training. It is process-level disambiguation capture.

## Analysis

### Two lawful operating modes

1. Narrow mode:
   configuration-heavy
   low ambiguity at execution time
   low per-transformation interpretation cost
   high reuse efficiency inside a constrained domain
   weak adaptability outside the configured envelope

2. Broad mode:
   light configuration
   high ambiguity at execution time
   high per-transformation interpretation cost
   lower immediate efficiency
   stronger ability to reach novel or weakly specified problems

This is the same tradeoff seen elsewhere in the repo:

- specification reduces ambiguity by moving truth upward into explicit constitutional surfaces
- design reduces ambiguity further by choosing concrete realization structure
- scenarios test whether the remaining ambiguity still permits real operational meaning

That chain is already explicit in [SPEC_METHOD.md](/Users/jim/src/apps/genesis_sdlc/specification/standards/SPEC_METHOD.md#L91) and in the requirement/design boundary at [SPEC_METHOD.md](/Users/jim/src/apps/genesis_sdlc/specification/standards/SPEC_METHOD.md#L119).

### The economic tradeoff

The core variable is where the system pays its disambiguation cost.

- In narrow mode, the cost is paid earlier through configuration, schema choice, constrained interfaces, explicit vectors, typed assets, or ratified design records.
- In broad mode, the cost is paid later during each transformation as the system interprets ambiguous language, missing structure, and local exceptions.

The tradeoff is therefore:

- more specificity up front gives cheaper repeated execution but overfits more easily
- more ambiguity up front gives broader reach but forces repeated interpretation work

If the system lacks memory, broad mode pays the same disambiguation tax again and again. Each run re-solves problems that should already be settled.

### Why memory matters

Memory changes the economics because it can convert repeated runtime disambiguation into reusable process structure.

The important point is that this is not "learning" in the training-weight sense. The system is not becoming universally smarter. It is becoming locally less ambiguous because prior resolutions are being carried forward.

Good memory should capture:

- accepted interpretations
- rejected interpretations
- stable project-local vocabulary
- prior boundary decisions
- known mappings from ambiguous requests to concrete process actions
- evidence that a prior disambiguation actually worked in practice

In repo terms, this sits naturally beside the constitutional chain rather than outside it:

- some remembered disambiguations stay local and ephemeral
- some become workspace conventions
- some become design records
- some deserve promotion into live specification if they are no longer optional

That is consistent with the ownership and anti-drift rules in [SPEC_METHOD.md](/Users/jim/src/apps/genesis_sdlc/specification/standards/SPEC_METHOD.md#L224) and [SPEC_METHOD.md](/Users/jim/src/apps/genesis_sdlc/specification/standards/SPEC_METHOD.md#L325).

### What the method should optimize for

The method should not try to eliminate ambiguity globally. It should decide which ambiguities are worth paying repeatedly and which should be collapsed into explicit structure.

That implies four principles:

1. Use narrow configuration where repetition is high and variance is low.
   If the same class of transformation happens often, pay the cost once and compile the ambiguity away.

2. Use broad transformation where exploration value is high and the problem class is still unstable.
   If the space is still being discovered, premature narrowing turns design guesses into accidental law.

3. Use memory to capture resolved ambiguity at the smallest valid scope.
   Do not immediately constitutionalize every resolution. Keep local resolutions local until repetition proves they are stable.

4. Promote repeated disambiguations upward only when they stop being optional.
   Once a resolution becomes necessary for coherence across runs, it belongs in design or specification rather than private memory.

### Failure modes

Two failure modes matter here.

First, over-configuration:

- too much early narrowing
- efficient execution
- poor adaptability
- local convenience mistaken for general law

Second, perpetual ambiguity:

- every run requires fresh interpretation
- progress remains expensive
- no accumulation of process clarity
- the system appears flexible but never becomes operationally cheaper

The right target is neither maximal rigidity nor maximal openness. It is controlled ambiguity reduction with promotion rules.

## Recommended Action

1. Add an explicit "ambiguity budget" concept to transformation design.
   For each transformation, say whether ambiguity is intended to be resolved by configuration, by runtime interpretation, or by a mixed strategy.

2. Define memory classes by authority level.
   Suggested split:
   constitutional memory
   design memory
   workspace memory
   run-local episodic memory

3. Require provenance on remembered disambiguations.
   A remembered interpretation should say where it came from, what evidence supported it, and whether it is local convention or ratified law.

4. Add a promotion rule.
   If the same ambiguity is resolved the same way repeatedly, that is pressure to move the resolution upward into design or specification.

5. Keep the distinction explicit:
   training changes model capability
   process memory changes local disambiguation cost

## Working Thesis

The system should be able to operate in both narrow and broad modes. Narrow mode buys execution efficiency by paying configuration cost early. Broad mode buys reach by paying interpretation cost per run. Memory is the mechanism that prevents broad mode from paying the same disambiguation cost forever. The system does not learn by weight update. It learns by converting repeated ambiguity into remembered process structure, then promoting stable structure upward when it becomes authoritative.
