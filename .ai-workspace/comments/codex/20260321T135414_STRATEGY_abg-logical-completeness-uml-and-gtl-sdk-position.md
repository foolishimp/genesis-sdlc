# STRATEGY: abiogenesis Logical Completeness, UML Coverage, and GTL as SDK

**Author**: Codex
**Date**: 2026-03-21T13:54:14
**For**: all

## Position

Yes: if `abiogenesis` is the kernel/TCP layer, then it has to be proven logically complete and robust at that layer.

That means the question is not only "does the current Python implementation work?" It is:

- is the abstract domain model closed?
- are the control/state transitions total and well-governed?
- can every path end in a truthful terminal condition?
- are failure, retry, blockage, override, and observation all first-class?

If you want confidence at that level, UML is the right next step.

## What Must Be Captured

To reason about `abiogenesis` as a kernel/runtime substrate, the minimum useful model set is:

1. **Domain model**
   Class-level structure of the core concepts and their invariants.

2. **State model**
   The lifecycle of a job, edge, iteration, and workflow execution.

3. **Sequence model**
   The actual control interactions between iterator, evaluators, workers, event bus, and projection logic.

Without all three, you can still describe the engine, but you cannot prove that its paths are coherent.

## UML Set

### 1. Domain/Class Diagram

This should cover the first-class objects:

- `Package`
- `Asset`
- `Edge`
- `Job`
- `Worker`
- `Operator`
- `Evaluator`
- `Rule`
- `Consensus`
- `Context`
- `Manifest`
- `Event`
- `Scope`
- `Projection`

The point is to make explicit:

- what is constitutional vs build-specific
- what is immutable vs runtime-derived
- what owns identity
- what owns custody
- what relationships are one-to-many vs derived

This is the diagram that shows whether the model itself is sound.

### 2. State Diagrams

At minimum:

- **Job/edge convergence state**
  `unknown -> fd_failing | fp_pending | fh_pending | converged`

- **Iterator state**
  `idle -> inspect -> bind_fd -> decide -> dispatch_fp | request_fh | report_fd_gap | converge`

- **Workflow state**
  `bootstrapped -> active -> blocked | converged | superseded | failed`

- **Manifest/provenance state**
  drafted, dispatched, assessed, superseded, revoked

These diagrams answer: are there ambiguous states, missing terminals, or illegal loops?

### 3. Sequence Diagrams

At minimum:

- `gen-start --auto`
- `gen-iterate`
- `bind_fd()`
- F_P dispatch and result assessment
- F_H approval path
- gap computation / projection path
- install/bootstrap path

These diagrams answer: who calls whom, in what order, under which guards, with what emitted evidence?

This is where hidden recursion, custody drops, and false observability usually become visible.

## Why This Matters

Your current kernel/TCP analogy implies a hard standard:

- a hop is either delivered,
- or it is known not to have been delivered,
- and the system can explain why.

That requires more than code coverage.

It requires proof that:

- every control path is modeled
- every terminal outcome is explicit
- every emitted event corresponds to a real state transition
- every blocking condition has a legal successor path
- there is no silent state loss between authored intent and runtime judgment

This is exactly why the recent `gsdlc` failure mattered: the hop machinery was present, but the routing layer loaded the wrong requirement surface. UML will not fix that by itself, but it makes those custody and path gaps far easier to detect before they ship.

## GTL's Place

The cleanest reading is:

- `abiogenesis` = runtime kernel/orchestration substrate
- `GTL` = SDK / type system / orchestration IR

That is, GTL is not the runtime itself.
It is the semantic construction kit used to define:

- graphs
- assets
- edges
- evaluators
- rules
- workers
- consensus and control surfaces

In that sense GTL is both:

1. **SDK**
   The authoring interface for defining a workflow system.

2. **IR**
   The portable representation that can be interpreted or compiled onto different runtimes.

This is an important distinction because it keeps you from collapsing:

- abstract workflow semantics
- engine runtime behavior
- build-specific realization

into one thing.

## Recommended Logical Stack

The most coherent stack is:

- **Spec layer**
  Domain model and behavioral invariants.

- **GTL layer**
  Typed SDK/IR used to express those invariants as executable graph structure.

- **abiogenesis layer**
  Reference runtime that executes GTL-defined workflows.

- **Build layer**
  Concrete tenants/runtimes such as Claude, Codex, AWS-native, local, distributed.

That separation gives you room to ask the right questions:

- Is the spec complete?
- Is GTL expressive enough?
- Is abiogenesis a correct interpreter/orchestrator?
- Is a given build a faithful realization?

## What "Logically Complete" Should Mean

For `abiogenesis`, logical completeness should mean:

1. Every first-class runtime concept is represented in the domain model.
2. Every legal state transition is explicit.
3. Every illegal transition is forbidden by model or guard.
4. Every terminal outcome is distinguishable:
   converged, blocked, failed, superseded, revoked.
5. Every decision point has an evidence surface:
   deterministic result, probabilistic assessment, human approval, or recorded override.
6. Every emitted event corresponds to a modeled state change.
7. Every workflow path can be traced from authored constraint to observed runtime outcome.

That is the standard I would use to evaluate whether the kernel/TCP claim is actually earned.

## Recommended Deliverables

I would capture this as a deliberate reasoning pack:

1. UML class diagram for the constitutional domain model.
2. UML state diagrams for iterator, job, workflow, and manifest lifecycle.
3. UML sequence diagrams for the main execution paths and failure/approval branches.
4. A path-completeness checklist:
   every branch, terminal, failure mode, and evidence emission accounted for.
5. A GTL position note:
   GTL as SDK/IR, abiogenesis as runtime, builds as realizations.

## Conclusion

If `abiogenesis` is the kernel/TCP layer, then it should be specified and reviewed like a kernel:

- closed domain model
- explicit state machine
- auditable message flow
- no silent path gaps

And if `GTL` is really the SDK, that should be stated clearly:

- GTL defines the portable workflow semantics
- abiogenesis executes them
- builds realize them

That framing will let you reason about correctness at the right layer, and it will make later portability work much cleaner.
