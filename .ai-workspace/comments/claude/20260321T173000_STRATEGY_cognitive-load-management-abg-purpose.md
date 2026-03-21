# STRATEGY: ABG Purpose — Cognitive Load Management for Agentic Coders

**Author**: Claude Code (from user direction)
**Date**: 2026-03-21T17:30:00Z
**For**: all

---

## The Point

WiFi just works. TCP/IP just works. But underneath: decades of complexity — retransmission timers, congestion windows, half-open detection, sequence numbers, checksums, flow control, connection state machines. None of this is visible to the user opening a browser.

ABG is the same pattern. The formal gap analysis (`20260321T160000_SCHEMA`) identifies 20 gaps across 6 theoretical lenses — category theory, sheaf theory, temporal logic, event calculus, TCP protocol analysis, agile delivery. That is complexity **for** reliability, not complexity **for** its own sake.

## What the stack manages on behalf of the agentic coder

The table below separates what the **kernel** (abg) handles from what the **orchestrator** (commands/gen_start) and **service layer** (gsdlc) handle. Items marked *(ABG 1.0 target)* are proposed hardening items not yet implemented — see the formal gap analysis for status.

| Concern | What the LLM agent would otherwise have to track | What handles it | Layer |
|---------|--------------------------------------------------|----------------|-------|
| **What to work on** | Scan all edges, determine which has gaps, pick one | `gen_iterate` selects first unconverged job in topological order | Orchestrator (commands) |
| **What constraints apply** | Remember which spec, design, ADRs are relevant to this edge | `Edge.context` binds the observer model per hop | Kernel (abg) |
| **Whether work is done** | Evaluate all acceptance criteria, track partial progress | F_D evaluators compute delta deterministically | Kernel (abg) |
| **Whether prior work is still valid** | Remember what was certified, under which spec version, whether context changed | `certified` fluent with spec_hash. *(ABG 1.0 target: + context digest, EC3)* | Kernel (abg) |
| **Whether approval was given** | Track human decisions across sessions, versions, revocations | `operative` fluent with carry-forward across workflow versions | Kernel (abg) |
| **What to do when stuck** | Decide whether to retry, escalate, or wait | F_D → F_P → F_H escalation chain with explicit gates | Kernel (abg) |
| **Whether a dispatch is orphaned** | Remember what was sent, whether a response came back | *(ABG 1.0 target: `pending` fluent with `stale_after_ms`, EC1)* | Kernel (abg) |
| **Under which law work happened** | Track which Package version was active when each event was emitted | *(ABG 1.0 target: `PackageSnapshot.work_binding()` enforced on every work event, A1)* | Kernel (abg) |
| **Whether the problem is actually solved** | Judge whether tests prove the system solves the problem, not just that code is self-consistent | *(ABG 1.0 target: ObserverModel = spec + design as observation surface, B.1)* | Service (gsdlc) |
| **Which workflow to route intent through** | Decide whether this is an SDLC task, PoC, discovery, or research | *(Post-1.0 target: CompositionSet routing)* | Service (gsdlc) |
| **Outer loop termination** | Decide when to stop iterating across edges | `gen_start --auto` with `max_iterations` bound | Orchestrator (commands) |

Every row is cognitive load that the LLM agent currently carries in its context window. Every row is a source of error when the context window fills, compresses, or hallucinates. The stack moves these concerns from the agent's volatile context into deterministic, auditable, replayable infrastructure — kernel for hop-level reliability, orchestrator for loop control, service layer for routing and composition.

## The analogy is precise

| Layer | Network | Genesis |
|-------|---------|---------|
| **Physical** | Ethernet, radio | File system, event stream, MCP transport |
| **Link** | Frames, MAC addressing | Event records, workspace territory |
| **Network (IP)** | Routing, addressing, fragmentation | gsdlc — route intent through graph, feature vectors, profiles |
| **Transport (TCP)** | Reliable delivery, flow control, congestion | **ABG** — reliable hop, convergence, gating *(1.0 target: + orphan detection, context invalidation)* |
| **Application** | HTTP, SMTP, DNS | The agentic coder — writes code, runs tests, produces designs |

The application layer (the LLM agent) doesn't think about retransmission timers. It makes a request and gets a reliable response. TCP handles the rest. After ABG 1.0, the agentic coder won't think about whether its F_P certification is stale or whether a dispatch was orphaned. ABG will handle the rest.

## Why this matters now

The formal analysis is not academic exercise. Every gap identified is a place where **complexity currently leaks upward** — where the agentic coder has to compensate for something the kernel should handle but doesn't yet:

- **EC3 (stale certifications)**: Today, the agent must remember what context it was certified under and manually re-evaluate when context changes. ABG 1.0 target: context-digest invalidation makes this automatic.
- **EC1 (orphaned manifests)**: Today, the skill layer must track whether a dispatch is in flight. ABG 1.0 target: the pending fluent makes orphan detection structural.
- **A1 (lawless events)**: Today, replay requires the agent to infer which law was active. ABG 1.0 target: PackageSnapshot binding on every work event.
- **S1 (custody failure)**: Today, the agent evaluates against the wrong requirements and doesn't know it. That's not just cognitive load — it's invisible misdirection. ABG 1.0 target: custody fix (Phase 1).

Each fix moves complexity downward — from the agent's volatile context into deterministic infrastructure. The agent gets simpler. The system gets more reliable. WiFi just works.

## Design principle

**Complexity is not the enemy. Unmanaged complexity is the enemy.**

ABG's job is to absorb complexity so the agentic coder doesn't have to. Every primitive, every fluent, every evaluator, every gate is complexity **in service of** a simple interface: "here is a job, here is the context, here are the acceptance criteria — produce the artifact."

The 20 gaps in the formal analysis are not "the system is too complex." They are "the system is not yet complex enough in the right places" — the complexity that should be in the kernel is still leaking into the agent.

When ABG 1.0 ships with these fixes, the agent's interface is:
1. Receive a job with bound context
2. Produce an artifact
3. The kernel handles everything else — convergence, certification, invalidation, orphan detection, replay, provenance

That's WiFi. That's TCP. That's the point.
