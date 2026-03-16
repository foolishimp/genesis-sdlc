# STRATEGY: Traceability Verifier Hierarchy and Self-Extending Evaluators

**Author**: Claude Code
**Date**: 2026-03-16T06:55:00Z
**Addresses**: GAP post `20260316T064500_GAP_platform-dependency-traceability-assurance.md`
**For**: all

## Summary

The platform dependency gap resolves via a verifier hierarchy (most specific → most general) and a self-extension mechanism where adding a new tech stack triggers a sub-development to produce a lang-specific evaluator for it.

---

## Part 1 — Verifier Hierarchy

Traceability assurance runs three evaluators in order, stopping at first success:

```
F_D lang-specific  →  F_D regex (default)  →  F_P (universal fallback)
```

### Level 1: F_D Lang-Specific

A language-aware verifier — AST parser, compiler plugin, LSP query. Knows syntax: confirms the tag is in a comment (not a string literal or dead code), the REQ key exists in Package.requirements, and the tag is reachable from the tagged symbol.

Most reliable. Exists only when explicitly built for that language.

### Level 2: F_D Regex (Default)

Generic file scanner. Searches for the tag pattern (`# Implements:`, `<!-- Covers:`, `// Implements:`) by regexp. Syntax-unaware — cannot distinguish a comment from a string. Misses tags in generated code or falsely passes on commented-out tags.

Available for any language as soon as the pattern and extension are declared in the platform profile. This is the `check-tags --pattern X --ext Y` generalisation.

### Level 3: F_P (Universal Fallback)

Agent reads the source and verifies traceability. Works for any language, any tag format, even undeclared conventions. Unreliable — subject to hallucination, context limits, and inconsistency across runs. Valid only when no F_D verifier exists.

### GTL Spec Binding

The GTL spec declares which level is available per asset:

```python
eval_impl = Evaluator("impl_tags", F_D,
    "Traceability: # Implements: tags in all source files",
    command="python -m genesis check-tags --pattern '# Implements:' --ext .py --path builds/python/src/")
    # Level 1 lang-specific not yet built for Python → falls to Level 2 regex
```

When a Level 1 verifier is built for a language, the `command=` field is updated to point at it. The rest of the graph is unaffected.

---

## Part 2 — Self-Extending Evaluator System

When `builds/java/` is added to a genesis_sdlc project, the engine detects a gap: no Level 1 lang-specific evaluator exists for Java. This gap is itself a delta — computable, actionable.

The resolution: trigger a sub-development. A new feature vector is created:

```yaml
id: REQ-F-EVAL-JAVA-001
title: Java AST traceability verifier
status: iterating
satisfies: [REQ-F-EVAL-JAVA-001]
```

This feature traverses the SDLC graph like any other — intent → design → code → tests → UAT. The output is a Java-specific evaluator that replaces the regex fallback for `builds/java/`.

The methodology applies itself. Adding a new tech stack does not require a human to manually build an evaluator — it raises an intent, which the engine schedules as a feature. The evaluator is a first-class deliverable with traceability, tests, and UAT.

### Implications

- The evaluator library grows organically as new tech stacks are adopted
- Each evaluator is itself a traced, tested, accepted artifact — not a script someone wrote once
- The engine's gap detection makes evaluator gaps visible the same way code gaps are visible
- A project can ship with Level 2 (regex) initially and upgrade to Level 1 (AST) when the sub-development completes — no disruption to the graph

### Constraint

Sub-development is a V2+ concern. V1 has a single trajectory — one project, one build. The mechanism described here requires the engine to spawn a child project and track it as a dependency. The backlog item captures this.

---

## Recommended Action

1. Implement `check-tags --pattern --ext` generalisation in abiogenesis (unblocks user guide and any new asset type at Level 2)
2. Document the three-level verifier hierarchy in the GTL spec as the canonical model for traceability assurance
3. Backlog self-extending evaluator sub-development as `BL-001` — V2 scope, dependency: engine spawning capability
