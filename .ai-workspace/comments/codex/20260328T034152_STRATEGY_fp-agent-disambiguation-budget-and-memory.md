# STRATEGY: F_P Agent Disambiguation Budget And Memory

**Author**: codex
**Date**: 2026-03-28T03:41:52+1100
**Addresses**: F_P transformers and evaluators executed by coding agents with shell, tools, and discovery capacity
**Status**: Draft

## Summary

The important unit here is not "an LLM" in the abstract. It is an F_P agent operating on an edge.

That agent is embodied:

- it runs in a shell
- it has tools
- it can inspect the repo
- it can discover structure beyond the literal prompt it was given

That means the real design question is: how much ambiguity should an F_P edge leave for the agent to resolve at runtime, and how much should be collapsed up front into manifests, schemas, prompts, and constraints.

If the edge is tightly configured, the agent spends less time discovering and disambiguating on each run. Reuse gets cheaper, faster, and more predictable, but the task envelope narrows. If the edge is loosely configured, the agent can discover more and adapt to wider contexts, but every run pays a fresh disambiguation cost. The method should support both, and memory should capture resolved disambiguations so the same edge does not pay the same discovery cost forever.

This is not training. It is process-level narrowing of ambiguity through remembered prior resolutions.

## Analysis

### F_P is an agentic surface

For this repo, an F_P transformer or evaluator is not just "generate some text."

It is closer to:

- receive intent and edge context
- inspect the available specification, design, code, and evidence surfaces
- use tools to discover what is actually present
- make bounded judgments or produce bounded transformations
- emit output or assessment back into the process

That makes ambiguity an explicit operational cost.

When an F_P edge is under-specified, the agent must spend runtime effort on:

- interpreting vague intent
- discovering the relevant files and boundaries
- inferring missing structure
- deciding which tools to use
- deciding when enough context has been gathered

Some of that is valuable exploration. Some is repeated waste.

### The tradeoff is between configuration cost and discovery cost

There are two lawful modes.

1. Tight F_P configuration

- more explicit manifesting up front
- narrower allowed tool use or search space
- stronger boundary conditions
- lower runtime disambiguation cost
- better repeatability
- narrower problem envelope

2. Loose F_P configuration

- lighter manifesting up front
- more freedom to search, inspect, and infer
- higher runtime disambiguation cost
- better adaptability to novel or weakly structured situations
- broader problem envelope

This is not a moral choice between "good discipline" and "good flexibility." It is an economic choice about where the process pays its ambiguity bill.

### Transformer and evaluator have different ambiguity needs

The distinction matters.

An F_P transformer often benefits from a wider discovery budget because construction usually needs contextual discovery:

- what code already exists
- what local conventions matter
- what interfaces are actually stable
- what tests or release surfaces already constrain the work

An F_P evaluator should usually be tighter.

If an evaluator is too ambiguous, it can silently turn local interpretation into accidental law. Evaluators should generally operate against narrower evidence protocols, clearer criteria, and smaller search spaces than transformers.

So the question is not just "how much ambiguity?" It is "how much ambiguity is lawful for this edge role?"

### Memory is how the process stops paying the same ambiguity cost repeatedly

Without memory, a broad F_P edge re-discovers the same local facts every time:

- repo layout
- naming conventions
- preferred commands
- accepted evidence shapes
- local interpretations of vague operator language

That keeps the system flexible, but it also keeps it expensive.

Memory changes the economics. It lets the process retain prior disambiguations and reuse them later.

The key distinction is:

- training changes model capability
- memory changes local process ambiguity

The model does not become universally smarter. The edge becomes locally cheaper to run because some uncertainty has already been resolved.

### What memory should capture

Useful F_P memory is not just "facts." It is resolved process ambiguity.

That includes:

- mappings from vague intents to concrete task shapes
- repo-local path and boundary knowledge
- tool-selection heuristics that actually worked
- accepted interpretations of edge criteria
- known failure modes and their effective probes
- stable local conventions that do not yet deserve promotion into design or specification

The memory question is also a scope question.

Some memory should be:

- run-local
- workspace-local
- edge-local
- reusable across similar projects

Not all remembered disambiguation deserves constitutional promotion.

### Promotion rule

Memory is useful precisely because it should not immediately become law.

But if the same ambiguity is repeatedly resolved the same way, the process should ask whether that resolution is still optional.

When it stops being optional, it should move upward:

- into edge configuration
- into design
- into specification if it becomes constitutional

That is how the system tightens over time without confusing local heuristics with ratified authority.

## Recommended Action

1. Add an explicit ambiguity budget to F_P edge design.
   Each transformer or evaluator should declare how much discovery it is expected to perform versus how much structure is pre-specified.

2. Add a discovery budget.
   Say what the agent is allowed to inspect: specific files, a subtree, the full repo, external evidence, or no discovery beyond manifest inputs.

3. Treat transformer and evaluator budgets differently.
   Transformers can usually tolerate wider discovery. Evaluators should default narrower.

4. Add process memory for disambiguation, not just history.
   Store prior resolutions that reduce future search and interpretation cost.

5. Add a promotion trigger.
   Repeatedly reused disambiguations should be reviewed for promotion into edge manifests, design records, or live specification.

## Working Thesis

An F_P edge is an agentic runtime surface, not a static prompt. Its cost depends on how much ambiguity the agent must resolve through shell access, tool use, and discovery. Tight configuration lowers per-run cost but narrows the edge. Loose configuration broadens the edge but increases runtime discovery cost. A good method uses both modes deliberately and adds memory so repeated disambiguation becomes remembered process structure rather than being paid from scratch on every run.
