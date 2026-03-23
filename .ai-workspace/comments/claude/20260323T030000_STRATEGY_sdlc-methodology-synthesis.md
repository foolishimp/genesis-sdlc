# STRATEGY: SDLC Methodology Synthesis

**Author**: Claude
**Date**: 2026-03-23T03:00:00+11:00
**Addresses**: sdlc_graph.py, specification/, specification/standards/, builds/python/design/
**For**: all
**Status**: DESIGN PROPOSAL — nothing implemented until approved

---

## The problem

The SDLC graph has accumulated three structural debts:

1. **Pipeline topology** — edges 7-9 form a linear chain where real dependencies are a DAG
2. **Bootloader treated as source** — it's a derived document that goes stale, but every edge reads it as truth
3. **Intermediate assets are checkboxes** — feature_decomp and module_decomp don't produce structured, validatable artifacts (dependency DAGs, build schedules, priority ordering)

These are not independent problems. They share a root cause: **the graph doesn't model where its own authority comes from**.

---

## Source of truth

Three authored document planes constitute the authority:

| Plane | Location (source repo) | Location (installed project) | What it governs |
|-------|----------------------|---------------------------|----------------|
| **Specification** | `specification/` | `specification/` | WHAT — intent, requirements, feature decomposition |
| **Standards** | `specification/standards/` | `.gsdlc/release/operating-standards/` | HOW TO WRITE — conventions, writing style, spec format, release process, user guide format, backlog format |
| **Design** | `builds/python/design/adrs/` | `design/adrs/` | HOW TO BUILD — architecture decisions, tech stack, interfaces |

Everything else is **derived**:

| Derived artifact | Derived from | Staleness risk |
|-----------------|-------------|----------------|
| **Bootloader** (CLAUDE.md / SDLC_BOOTLOADER.md) | Spec + Standards + Design | Goes stale when any source changes |
| **User guide** (docs/USER_GUIDE.md) | Design + Integration proof | Goes stale on new features or version bumps |
| **Feature vectors** (.ai-workspace/features/) | Requirements | Goes stale when requirements change |
| **Module graph** (.ai-workspace/modules/) | Design ADRs + Feature vectors | Goes stale when design changes |
| **Build schedule** (.ai-workspace/features/build_schedule.json) | Feature DAG + Priority strategy | Goes stale when features change |

---

## The graph

A DAG. 11 assets (bootloader added), 10 edges. Derived assets have multi-source lineage.

```
              intent
                |
           requirements -------------------------+
                |                                 |
         feature_decomp                           |
                |                                 |
             design ----------------+             |
                |                   |             |
          module_decomp             |             |
                |                   |             |
              code --------+        |             |
                |          |        |             |
           unit_tests      |        |             |
                |          v        v             |
                +-> integration   user     bootloader
                      _tests      _guide        |
                        |           |            |
                        +-----+-----+------------+
                              |
                          uat_tests
```

### Assets

| Asset | ID format | Lineage (derived from) | Markov conditions |
|-------|-----------|----------------------|-------------------|
| intent | INT-* | — | problem_stated, value_proposition_clear, scope_bounded |
| requirements | REQ-* | intent | keys_testable, intent_covered, no_implementation_details |
| feature_decomp | FD-* | requirements | all_req_keys_covered, dependency_dag_acyclic, mvp_boundary_defined, build_schedule_defined, priority_strategy_applied |
| design | DES-* | feature_decomp | adrs_recorded, tech_stack_decided, interfaces_specified, no_implementation_details |
| module_decomp | MOD-* | design | all_features_assigned, dependency_dag_acyclic, build_order_defined |
| code | CODE-* | module_decomp | implements_tags_present, importable, no_v2_features |
| unit_tests | TEST-* | code | all_pass, validates_tags_present |
| integration_tests | ITEST-* | code | sandbox_install_passes, e2e_scenarios_pass |
| bootloader | BOOT-* | spec + standards + design | spec_coverage_current, standards_reflected, graph_topology_accurate |
| user_guide | GUIDE-* | design + integration_tests | version_current, req_coverage_tagged, content_certified |
| uat_tests | UAT-* | requirements + user_guide + integration_tests + bootloader | accepted_by_human |

### Edges

| # | Edge | Source(s) | Target | Evaluators | Gate |
|---|------|----------|--------|-----------|------|
| E1 | intent -> requirements | intent | requirements | F_H: intent approved | Human |
| E2 | requirements -> feature_decomp | requirements | feature_decomp | F_D: req coverage, DAG acyclic, schedule valid. F_P: decompose + schedule. F_H: approve | Human |
| E3 | feature_decomp -> design | feature_decomp | design | F_P: ADRs coherent. F_H: approve | Human |
| E4 | design -> module_decomp | design | module_decomp | F_D: module coverage. F_P: decompose. F_H: approve | Human |
| E5 | module_decomp -> code | module_decomp | code | F_D: impl tags. F_P: code complete | — |
| E6 | code <-> unit_tests | code, unit_tests | unit_tests | F_D: tests pass, validates tags, e2e exists. F_P: coverage complete | — |
| E7 | code -> integration_tests | code, unit_tests | integration_tests | F_D: sandbox report. F_P: sandbox run | — |
| E8 | spec+standards+design -> bootloader | requirements, design, integration_tests | bootloader | F_D: spec coverage, graph accuracy. F_P: regenerate. F_H: approve | Human |
| E9 | design+integration -> user_guide | design, integration_tests | user_guide | F_D: version, req coverage. F_P: content. F_H: approve | Human |
| E10 | evidence -> uat_tests | requirements, user_guide, integration_tests, bootloader | uat_tests | F_H: human accepts | Human |

### What changed from the old graph

1. **integration_tests** sources from `[code, unit_tests]` not `unit_tests` alone — you test the code, not the test suite
2. **user_guide** sources from `[design, integration_tests]` not `integration_tests` alone — you document the design, verified by integration proof
3. **bootloader** is a new asset — derived from spec + standards + design, subject to iteration, validated for currency
4. **uat_tests** sources from `[requirements, user_guide, integration_tests, bootloader]` — acceptance criteria from spec, evidence from guide + sandbox + bootloader currency

---

## Feature decomp produces structured artifacts

Feature decomp is not a checkbox. It produces:

**Per-feature YAML** (`.ai-workspace/features/active/FD-NNN.yml`):
```yaml
id: FD-001
name: auth-flow
satisfies: [REQ-F-AUTH-001, REQ-F-AUTH-002]
depends_on: []  # other FD-* ids
```

**Build schedule** (`.ai-workspace/features/build_schedule.json`):
```json
{
  "priority_strategy": "steel_thread",
  "mvp_boundary": ["FD-001", "FD-003"],
  "schedule": [
    {"id": "FD-001", "depends_on": [], "priority_score": 9, "rationale": "touches all layers"},
    {"id": "FD-003", "depends_on": ["FD-001"], "priority_score": 7, "rationale": "core storage"}
  ]
}
```

**F_D validates**:
- Every REQ key covered by at least one feature
- Dependency DAG is acyclic
- Build schedule respects depends_on ordering
- Priority strategy is one of the recognized set

**Priority strategies** (declared in INTENT.md):

| Strategy | What it means | When to use |
|----------|--------------|-------------|
| steel_thread | Thin E2E slice proving architecture first, then fan out | New architecture, unproven stack |
| risk_first | Highest uncertainty first, kill unknowns early | Complex domain, many unknowns |
| dependency_first | Topological sort, leaves first | Well-understood domain |
| value_first | Business value / effort, highest ROI first | Time-to-market pressure |
| walking_skeleton | All features at minimal depth, then deepen | Large system, integration risk |

---

## Bootloader as derived asset

The bootloader (CLAUDE.md methodology content + SDLC_BOOTLOADER.md) is a synthesis of:
- **Specification**: graph topology, territory model, evaluator chain
- **Standards**: operating conventions, writing style, command reference
- **Design**: ADR summaries, tech stack, interface patterns

It serves one purpose: **cold-start orientation** for a new agent session.

Because it's derived, it goes stale. Making it a graph asset means:
- **F_D** checks it's current: spec coverage, graph topology matches actual graph, standards version matches
- **F_P** regenerates it when source documents change
- **F_H** approves the synthesis before it becomes the cold-start document

The bootloader edge fires after integration_tests (the system works) and reads from requirements + design (the spec/design are stable). This means no agent session operates on a stale bootloader — it gets validated in the same iteration loop as everything else.

---

## Context model

Edges reference **source documents**, not derived summaries:

| Context | Locator (runtime) | Used by edges |
|---------|-------------------|---------------|
| spec_intent | specification/INTENT.md | E1, E2, E3, E10 |
| spec_requirements | specification/requirements.md | E2, E3, E4, E5, E6, E7, E8, E9, E10 |
| spec_features | specification/feature_decomposition.md | E3, E4 |
| operating_standards | .gsdlc/release/operating-standards/ | E1, E8, E9 |
| design_adrs | design/adrs/ | E4, E5, E6, E8, E9 |
| features_dir | .ai-workspace/features/ | E2 |
| modules_dir | .ai-workspace/modules/ | E5 |

The bootloaders (`gtl_bootloader`, `sdlc_bootloader`) are **removed as contexts**. They are outputs of the iteration process, not inputs. The agent reads the source documents directly.

---

## What this design does NOT cover

- **Engine changes** (ABG): processing features in schedule order requires engine support for build schedules. That's ABG work, not graph work.
- **Installer changes**: the installer needs to scaffold `specification/INTENT.md` with a `priority_strategy:` field. Minor.
- **Bootloader generation**: the F_P evaluator for the bootloader edge needs to know how to synthesize CLAUDE.md content from spec + standards + design. That's a prompt, not code.
- **Graph variant profiles** (ADR-012): steel_thread vs walking_skeleton affects which edges fire and in what order — this interacts with the variant/projection system.

---

## Decision requested

Is this the right shape? Specifically:

1. Bootloader as a graph asset with F_D/F_P/F_H — yes/no?
2. Bootloaders removed as edge contexts (agents read source docs directly) — yes/no?
3. Feature decomp producing build_schedule.json with priority strategy — yes/no?
4. DAG topology for edges 7-10 — yes/no?
