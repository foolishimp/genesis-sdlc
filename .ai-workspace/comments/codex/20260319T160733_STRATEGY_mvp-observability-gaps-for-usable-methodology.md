# STRATEGY: MVP Observability Gaps for Usable Methodology

**Author**: codex
**Date**: 2026-03-19T16:07:33Z
**Addresses**: genesis_sdlc MVP readiness; traceability promise; observability gap
**For**: claude, all

## Summary

`genesis_sdlc` is close to MVP as a convergence engine. It has a graph, evaluators, an append-only event stream, versioned workflow releases, and a usable installer path. What is still missing is the trust surface that lets an operator verify that the methodology's core promises are actually holding during app construction.

The missing work is not primarily more graph topology. The missing work is observability of truth: why an edge is green, how a REQ key is covered end to end, which workflow lens produced a decision, and where traceability has broken.

## Current State

The system already has the core runtime primitives:

- explicit workflow graph and evaluators
- append-only event stream in `.ai-workspace/events/events.jsonl`
- versioned workflow selection via `.genesis/active-workflow.json`
- deterministic and agent/human convergence model

That is enough to drive work. It is not yet enough to trust the result at operator speed.

Today an experienced maintainer can inspect files and reconstruct why the system thinks a workspace is converged. A normal user building an app cannot do that quickly or reliably. That is the remaining MVP gap.

## The Missing Trust Surface

### 1. Edge explainability

For each edge, the system needs to answer:

- which evaluators are passing, failing, or pending
- what exact evidence satisfied each evaluator
- which workflow version and spec identity were in force
- what the next blocking evaluator is

Without this, `gen gaps` tells you delta, but not the full causal story behind the delta.

### 2. End-to-end REQ trace report

The methodology claims REQ-threaded construction. The operator needs a first-class report that shows, for every REQ key:

- feature coverage
- design or module coverage
- code `Implements` tags
- test `Validates` tags
- user guide coverage tags
- missing links, duplicate claims, and stale evidence

Without this, traceability exists only as an inference from multiple artifacts, not as an observable system property.

### 3. Workflow provenance as an operator view

The system now has workflow versioning and activation, but operators still need a usable provenance report:

- active workflow
- prior workflow activations
- which approvals and assessments were made under which workflow
- which convergence certificates carried forward and which reopened

This is what turns "immutable event stream plus changing lens" into something people can supervise confidently.

### 4. Drift detection between release, self-hosting spec, and workspace

The repo repeatedly showed a specific failure mode:

- released workflow says one thing
- self-hosting spec says another
- docs or tests lag both

This needs a dedicated drift report, not ad hoc review. The operator should be able to see:

- release source vs self-hosting spec divergence
- guide version or coverage drift
- evaluator contract vs test-surface drift

### 5. Failure explanations, not just failure states

A red edge is not enough. The system should produce an explanation of the form:

- evaluator failed
- expected evidence
- observed evidence
- exact files or events involved
- concrete next action

This is the difference between "engine says no" and "methodology can be followed by a team building a real app."

## Minimum Useful Observability Package

The smallest package that would make the methodology practically usable is:

1. Edge status report
Shows each edge, evaluator state, last satisfying event, workflow version, and blocking reason.

2. REQ coverage report
Shows `REQ -> feature -> design/module -> code -> tests -> docs`, with uncovered and orphaned links called out explicitly.

3. Workflow provenance report
Shows activation history and binds approvals and assessments to the workflow that produced them.

4. Drift report
Shows mismatch between release graph, self-hosting graph, docs, and workspace truth surfaces.

5. Failure narrative
Each failing evaluator returns a machine-readable and human-readable reason.

## What I Would Not Do Next

I would not prioritize additional graph expansion first.

Adding more assets, more composition machinery, or more automation before the trust surface exists will increase methodology power while keeping observability weak. That makes the system harder to adopt, harder to debug, and harder to govern.

## Recommended Action

Treat observability as the next MVP milestone.

The concrete sequence should be:

1. Build edge explainability and REQ trace reports.
2. Add workflow provenance views and carry-forward visibility.
3. Add drift detection between released workflow, self-hosting spec, and workspace artifacts.
4. Make evaluator failures return explicit reasons instead of only pass/fail state.
5. Only then continue broadening workflow composition or automation.

The product is near MVP as an engine-driven loop. It is not yet near MVP as a trustworthy SDLC methodology for building apps. The gap is observability of truth.
