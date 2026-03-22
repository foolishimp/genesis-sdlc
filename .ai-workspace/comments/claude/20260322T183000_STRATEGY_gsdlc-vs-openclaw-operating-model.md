# STRATEGY: GSDLC as Operating Model — Positioning Against AI Assistant Platforms

**Author**: claude
**Date**: 2026-03-22T18:30:00Z
**Addresses**: Project positioning, INT-001, marketplace conventions
**For**: all

## Summary

Analysis comparing GSDLC's convergence-driven methodology against OpenClaw (open-source AI assistant platform). GSDLC is not a competing product — it is the **corporate operating model** that tools like OpenClaw, Claude Code, Codex, and Gemini execute within. This framing clarifies what GSDLC is and what it is not.

## The Layer Distinction

```
┌─────────────────────────────────────────────┐
│  User Layer: OpenClaw / Claude Code / Codex  │
│  "Talk to me on Discord/Slack/Telegram"      │
│  Message routing, streaming, tool execution  │
├─────────────────────────────────────────────┤
│  Methodology Layer: GSDLC                    │
│  "Is this software converging on intent?"    │
│  Typed graphs, evaluator escalation, delta   │
├─────────────────────────────────────────────┤
│  Engine Layer: Abiogenesis (GTL)             │
│  "Run the convergence loop"                  │
│  Event stream, projection, scheduling        │
└─────────────────────────────────────────────┘
```

OpenClaw, Claude Code, Codex, Gemini — these are all employees. Smart, capable, but they show up each day and respond to whatever's in front of them. No one's checking if the aggregate work is converging. No one's gating quality before escalating to expensive resources. No one's threading traceability from intent to delivery.

GSDLC is the org chart, the review process, the definition of done, and the audit trail — all expressed as executable, typed code rather than a wiki page no one reads.

## Architecture Comparison

### State Model
| | GSDLC | OpenClaw |
|---|---|---|
| **Source of truth** | Append-only event stream (`events.jsonl`) | Session transcripts (JSONL) + gateway state |
| **State derivation** | Deterministic projection — `project(stream, type, id)` always returns same result | Mutable — sessions, config, plugin state are read-write |
| **Recovery** | Replay the event log | Reconnect to session; no formal replay guarantee |
| **Determinism guarantee** | Yes — core invariant | No — LLM responses are inherently non-deterministic |

### Agent Orchestration
| | GSDLC | OpenClaw |
|---|---|---|
| **Agent scope** | Tightly constrained — agent receives a `BoundJob` with curated context, spec, and output contract | Loosely constrained — agent gets conversation history + tool access |
| **When agents fire** | Only after F_D (deterministic) passes — never wastes agent budget on broken state | On every inbound message — no pre-filtering |
| **Agent output** | Typed artifacts that F_D evaluates on next cycle | Free-form text/tool calls streamed to user |
| **Multi-agent** | Territory model, schedule() detects conflicts | Routing rules map channels → agents; agents are isolated by session |

### Quality & Convergence
| | GSDLC | OpenClaw |
|---|---|---|
| **Completeness check** | Formal: `delta(state, constraints) = 0` means done | None — conversation never "converges" |
| **Evaluator escalation** | F_D → F_P → F_H (deterministic → agent → human) | No layered evaluation; LLM responds directly |
| **Human gates** | First-class (`F_H` evaluators, approval events, proxy mode) | No formal gates; user reads and reacts |
| **Traceability** | REQ keys thread intent → requirements → code → tests | None — messages are ephemeral conversations |

## What GSDLC Has That They Lack
- **Formal convergence** — a computable answer to "are we done?"
- **Evaluator escalation** — deterministic before probabilistic before human
- **Spec-as-code** — the GTL Package IS the specification
- **Traceability threading** — REQ keys from intent through tests
- **Deterministic replay** — reconstruct any historical state from the event log
- **Budget efficiency** — agents only called when deterministic checks pass

## What They Have That GSDLC Does Not Need
- Real-time conversational interface (20+ messaging channels)
- Streaming responses
- Tool ecosystem (browser automation, device control, etc.)
- Consumer-grade UX (onboarding wizard, companion apps)
- Plugin marketplace

These are employee capabilities. GSDLC doesn't need to chat on Discord — it needs to ensure that the agent chatting on Discord is doing the right work, in the right order, converging on the stated intent.

## Recommended Action

1. Use this framing in GSDLC documentation and positioning: GSDLC is the operating model, not a competing tool
2. Consider whether GSDLC should formally define an integration contract for AI assistant platforms (OpenClaw, Claude Code, etc.) as Workers
3. The F_D → F_P → F_H escalation ladder is the single strongest differentiator — emphasize it in intent
