> **Update**: MCP transport replaced by subprocess + env sanitization (ADR-022, 2026-03-23). Failure classification framework retained — transport is now `subprocess:claude-p`.

# Agent Failure Detection and the Governance Framework

**Category**: STRATEGY
**Date**: 2026-03-23
**Context**: Live F_P qualification testing, OpenClaw multi-agent framework analysis, test suite reliability incidents

---

## Thesis

The governance framework (GTL/SDLC graph, evaluators, convergence gradients) is the institution. Agents are workers. The framework must not constrain agent evolution, but it must detect when an agent is failing — the same way a well-run organisation detects when a human worker is struggling before the project collapses.

Investing in governance and process is valid. Standing in the way of agent evolution is not.

---

## Why Independent Agents

Agents are evolving faster than any chain-of-thought framework we could build around them. Today's Claude Code via MCP writes files, runs tests, navigates ambiguity. Tomorrow's agent may operate differently — different transport, different tool surface, different reasoning architecture.

The framework's value is not in prescribing how the agent works. It is in:

1. **Defining the work order** — the manifest prompt carries preconditions, current state, gap, context, output contract. This is the job description, not the implementation.
2. **Defining the acceptance criteria** — F_D evaluators check structural conformance deterministically. F_P evaluators check semantic quality via agent assessment. F_H gates capture persistent ambiguity requiring human judgment.
3. **Defining the escalation path** — F_D fails → F_P dispatched. F_P stuck → F_H escalated. F_H approved → back to F_D for the next edge. This is the organisational escalation chain.

The agent receives the manifest and full workspace access. What it does inside that boundary is its business. The framework only cares about the output and the convergence signal.

---

## Detecting Failed Agents: Lessons from Three Domains

### From Human Organisations

When a human worker is failing, well-run organisations detect it through:

| Signal | Detection Method | Response |
|--------|-----------------|----------|
| **No output** | Standup, sprint review — visible absence of deliverables | Check-in, pair, re-scope |
| **Wrong output** | Code review, QA gate, acceptance test | Feedback, rework cycle |
| **Slow progress** | Velocity tracking, burndown | Investigate blockers, reassign |
| **Stuck in a loop** | Same PR revised 5 times, same questions repeated | Escalate to senior, architectural review |
| **Silent failure** | Says "done" but downstream breaks | Post-mortem, add gate |
| **Scope creep** | Deliverable doesn't match the ask | Clarify spec, tighten acceptance criteria |

The key insight: **the organisation never inspects the worker's internal reasoning**. It inspects outputs at defined gates. The manager doesn't read the developer's mind — they read the PR, run the tests, check the deployment.

### From OpenClaw Multi-Agent Framework

OpenClaw tests agents without depending on their internal architecture:

1. **Probe-based validation**: Write a nonce → ask agent to read it → verify echo. Binary pass/fail, no ambiguity. Tests the agent's *capability*, not its *reasoning*.
2. **Tiered test suites**: Unit (mocked, fast) → E2E (real infra, controlled) → Live (real everything). Each tier tests a different layer of trust.
3. **Process isolation**: Each agent gets an isolated workspace, explicit cleanup, hard timeouts. A hung agent cannot poison the test harness.
4. **Error classification**: Distinguish provider failures (rate limit, timeout) from agent logic failures (wrong output, no output). Different failures get different responses.
5. **No MCP in the core loop**: Agent invocation is direct function call. MCP is an optional extension tested in isolation. Transport is not conflated with capability.

### From Our Own F_P Testing (Incidents)

The 51-minute hang during live F_P qualification exposed structural gaps:

1. **No timeout on MCP calls** — the agent ran, the MCP pipe died, pytest waited forever. A human manager would notice silence and check in.
2. **Self-seeding** — the test pre-created the artifact, then judged it. Like a manager accepting a report that was pre-written by the secretary.
3. **Protocol bypass** — convergence helpers emitted `assessed` events directly, skipping the iterate → result_path → assess-result chain. Like signing off on work without actually reviewing it.
4. **Silent pass** — manifest tests guarded assertions with `if returncode == 0`. Like a QA process that only runs when everything is already working.

---

## Actionable Framework for Agent Failure Detection

### 1. Timeout and Heartbeat

**Problem**: Agent runs indefinitely with no progress signal.
**Human analogy**: Worker goes silent for days.

```
Rule: Every F_P dispatch has a wall-clock timeout.
      Timeout → emit timeout event → escalate to F_H.
      No silent infinity.
```

Implementation: Add `timeout` parameter to `invoke_live_fp` and `_call_claude_code_mcp`. On timeout, archive whatever partial output exists, emit a `timeout` event, and return a failing result. The framework should treat timeout as "agent stuck" and escalate.

### 2. Output Presence Before Quality

**Problem**: Agent returns text but doesn't write artifacts to the expected location.
**Human analogy**: Worker submits a verbal update but no actual deliverable.

```
Rule: F_D checks artifact existence BEFORE F_P checks artifact quality.
      No artifact at expected path → F_P fails with "no deliverable".
      Never fall back to parsing the agent's conversational response.
```

Implementation: The mtime-based detection in `invoke_live_fp` is a step forward. But the judges should also distinguish "agent wrote nothing" from "agent wrote wrong thing". These are different failure modes requiring different responses.

### 3. Convergence Velocity

**Problem**: Agent produces output but delta doesn't decrease across iterations.
**Human analogy**: Worker keeps submitting revisions but the review comments don't decrease.

```
Rule: Track delta across iterations per edge.
      If delta unchanged after N iterations → escalate.
      The gradient must be non-zero or the system must stop.
```

Implementation: The event stream already has `delta_before` on each iterate. A monitor that compares `delta_before` across consecutive iterations on the same edge would detect stalls. This is analogous to a sprint burndown — if the line is flat, something is wrong.

### 4. Error Classification

**Problem**: All failures look the same — "test failed".
**Human analogy**: "The project is behind" doesn't tell you if the worker is sick, blocked, or incompetent.

```
Rule: Classify failures into:
      - transport_failure: MCP pipe died, timeout, process crash
      - no_output: Agent responded but wrote nothing
      - wrong_output: Agent wrote to wrong location or wrong format
      - quality_failure: Agent wrote structurally valid but semantically wrong output
      - stuck: Agent looping without progress
      Each class has a different response.
```

Implementation: The judge verdict should carry a `failure_class` field. Transport failures retry automatically. No-output failures get a more specific prompt. Wrong-output failures get structural feedback. Quality failures may just need another iteration. Stuck failures escalate.

### 5. Forensic Archive as Institutional Memory

**Problem**: When an agent fails, there's no record of what it tried.
**Human analogy**: Worker says "I tried everything" but there's no trail.

```
Rule: Every F_P dispatch archives:
      - manifest (the work order)
      - prompt (what the agent saw)
      - raw response (what the agent said)
      - artifact (what the agent wrote, if anything)
      - judge verdict (the quality assessment)
      - events (the full event chain)
      Regardless of pass/fail.
```

Implementation: Already in place via RunArchive. The improvement is to make archives queryable — not just directories, but a lightweight index that answers "which prompts produce which failure classes across runs?"

---

## What NOT to Do

1. **Don't constrain agent internals** — the manifest says what to produce, not how to produce it. If a future agent uses a different reasoning architecture, the framework shouldn't care.

2. **Don't replace MCP with direct API for F_P tests** — the whole point is testing agents with agency: tool access, workspace navigation, curiosity. Direct API tests prompt quality; MCP tests agent capability. These are different things.

3. **Don't hard-freeze the graph topology in tests** — the 9-edge topology is today's governance structure. Tests should verify the *pattern* (typed transitions, evaluator gates, convergence) not the specific edges. Edge-specific tests are provisional.

4. **Don't mock the agent** — a mocked agent tells you nothing about prompt sufficiency. The qualification test must use a real agent because the question is "can a capable agent succeed given this work order?" not "does our mock produce the right JSON?"

---

## Next Steps

| Action | Priority | Effort |
|--------|----------|--------|
| Add hard timeout to MCP calls with cleanup | High | Small |
| Add failure classification to judge verdicts | High | Medium |
| Add convergence velocity monitor to iterate | Medium | Medium |
| Build queryable archive index | Medium | Medium |
| Extract graph topology from tests into metadata | Low | Large |

---

*The framework is the institution. The agent is the worker. Test the institution's ability to detect and respond to failure — not the worker's internal reasoning.*
