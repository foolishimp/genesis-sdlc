# STRATEGY: Lessons from OpenClaw for ABG / GSDLC

**Author**: codex  
**Date**: 2026-03-24T11:20:53+11:00  
**For**: all

## Summary

OpenClaw is not doing the same job as ABG or GSDLC.

It is primarily:

- a gateway
- a session router
- an agent run host
- a multi-channel delivery system

ABG / GSDLC are trying to be:

- an event-sourced work system
- a convergence engine
- a lawful recursive graph runtime
- a construction system

So the value in studying OpenClaw is not that it solves the whole problem we are solving.

It does not.

The value is that it solves a smaller adjacent class of problems very well:

- hierarchical routing identity
- stable session addressing
- run lifecycle tracking
- streaming agent transport
- bounded structured leaf tasks

Those are useful lessons for ABG, as long as we do not collapse our richer model down to OpenClaw’s simpler one.

## What OpenClaw Actually Is

OpenClaw is best understood as a routed agent gateway.

The governing structure is:

- inbound message or tool request arrives
- request is mapped onto a session key
- session key resolves agent / workspace / channel context
- an agent run is launched or resumed
- streaming output is delivered back to the caller or channel

Useful references:

- `src/gateway/server-methods/agent.ts`
- `src/gateway/server-methods/agent-job.ts`
- `src/sessions/session-key-utils.ts`
- `src/gateway/sessions-resolve.ts`
- `docs.acp.md`

The center of gravity is not convergence.

It is routing and execution.

## How OpenClaw Handles Tasking

### 1. Session key as routed identity

OpenClaw routes work by `sessionKey`.

Examples from the docs:

- `agent:main:main`
- `agent:design:main`
- `agent:qa:bug-123`

ACP does not select agents directly. It routes by session key:

- `docs.acp.md`

Session keys are parsed structurally and support derived properties:

- agent scope
- chat type
- thread parent
- cron session
- subagent session
- ACP session

This is implemented in:

- `src/sessions/session-key-utils.ts`

So the identity pattern is:

- hierarchical
- human-readable
- structurally parseable
- used for routing and resumption

### 2. Session resolution ergonomics

OpenClaw resolves conversations by:

- explicit key
- session id
- label

This is implemented in:

- `src/gateway/sessions-resolve.ts`

That is important because it gives operators multiple ways to target the same routed unit without weakening the canonical routing identity.

### 3. Run identity and run lifecycle

OpenClaw distinguishes session identity from run identity.

The execution attempt is represented by `runId`.

Run lifecycle is tracked with:

- start
- end
- error
- timeout

And importantly, it has wait / dedupe / grace handling:

- transient error grace window
- cached terminal run snapshots
- waiters that subscribe to lifecycle events

This is implemented in:

- `src/gateway/server-methods/agent-job.ts`

This is one of the strongest things OpenClaw does.

### 4. Structured leaf tasks

OpenClaw also has an explicit bounded task surface in the bundled `llm-task` plugin:

- JSON-only prompt
- optional JSON Schema validation
- no tools
- explicit timeout
- temporary isolated run

This is implemented in:

- `extensions/llm-task/src/llm-task-tool.ts`
- `extensions/llm-task/README.md`

This is not a general construction engine.

It is a controlled leaf task primitive.

That distinction matters.

## Where OpenClaw Rhymes with Our Design

There are real structural rhymes.

### Hierarchical identity

OpenClaw session keys validate that hierarchical identity chains work well in production.

That rhymes with:

- `work_key`
- immutable lawful chains
- scope refinement by appending segments

Example analogy:

- OpenClaw: `agent:main:discord:channel:123`
- ABG/GSDLC: `INT-001/REQ-042/build.design/module.auth`

The shapes are not identical, but the principle is the same:

- the chain itself carries meaning
- the chain is routable
- the chain avoids needing opaque external lookup just to know what the work is about

### Work identity vs attempt identity

OpenClaw’s separation is:

- `sessionKey` = routed lane
- `runId` = one execution attempt

Our separation is:

- `work_key` = piece of work
- `run_id` = one attempt on that work

This rhyme is strong and worth preserving.

### Separation of routing from execution

OpenClaw does not confuse:

- how you address the work
- with how the agent run is executed

That is a good lesson for ABG too.

We should not confuse:

- `work_key`
- graph topology
- `iterate()`
- transport
- evaluator law

Each layer has a distinct responsibility.

## Where OpenClaw Diverges from Our Model

This is the more important part.

### 1. Session routing is not work convergence

OpenClaw’s `sessionKey` is a routing control.

It is not:

- an immutable event-sourced work identity
- a convergence unit
- a lawful projection key for recursive construction

It can be resolved, reset, rebound, or looked up by label.

That is correct for a conversation system.

It is not enough for an event-sourced work system.

### 2. No convergence engine

OpenClaw does not have:

- `delta`
- `F_D -> F_P -> F_H`
- certification as a stopping law
- revocation/carry-forward as the center of runtime behavior

It is not trying to answer:

- “what remains unconverged on this graph?”
- “which child work unit should be traversed next?”
- “has the parent converged because all descendants converged?”

### 3. No lawful recursive graph

OpenClaw does not have the class of mechanisms we are trying to recover:

- zoom morphism
- fragment composition
- spawn / fold-back
- child lineage as convergence law
- dynamic realized traversal over a lawful graph

It has session branching and subagent/session threading.

That is adjacent, but it is not the same thing.

### 4. Leaf tasking, not construction

The `llm-task` plugin is useful, but it is intentionally narrow:

- one prompt
- one JSON result
- one validation boundary

That is excellent for a leaf task.

It is not an alternative to:

- graph traversal
- recursive decomposition
- convergence-driven refinement

## Side-by-Side Comparison

### OpenClaw

- primary unit: session
- identity: `sessionKey`
- attempt: `runId`
- runtime: routed agent execution
- structure: channels, agents, sessions, plugins
- truth surface: live session + runtime state
- leaf task support: yes
- recursive convergence: no

### ABG / GSDLC

- primary unit: work
- identity: `work_key`
- attempt: `run_id`
- runtime: graph traversal under evaluator law
- structure: package, edge, job, fragment, work identity
- truth surface: event log + projection
- leaf task support: should exist
- recursive convergence: yes, or at least that is the intended direction

## What We Can Take from OpenClaw

### 1. Strong hierarchical addressing discipline

OpenClaw proves that hierarchical routed keys are practical and powerful.

What to take:

- keep `work_key` structured and readable
- parse it lawfully
- derive useful properties from the structure
- use refinement as a normal operation, not an exception

### 2. Clean separation between lane identity and attempt identity

OpenClaw is very clear that:

- the routed lane is one thing
- a specific run is another

That maps directly to:

- `work_key`
- `run_id`

We should preserve that split strongly.

### 3. Run lifecycle governance

The strongest reusable OpenClaw pattern is the run-lifecycle handling in `agent-job.ts`:

- cache terminal snapshots
- dedupe waiters
- tolerate transient error/failover windows
- distinguish timeout from hard failure

ABG would benefit from a similarly strong run-governance layer around F_P attempts.

This is especially relevant for:

- agent failure classification
- retry policy
- wait semantics
- post-dispatch observability

### 4. Bounded structured task tools

The `llm-task` plugin is a very good model for a bounded leaf task primitive.

What to take:

- explicit schema
- JSON-only contract
- no tools by default
- explicit timeout
- isolated attempt
- hard validation at the boundary

This is a very good pattern for:

- narrow sub-work
- leaf evaluative synthesis
- bounded helper transforms

It should not replace the graph.

It should sit inside it.

### 5. Operator-friendly targeting

OpenClaw’s resolution by:

- key
- id
- label

is operationally good.

ABG/GSDLC can learn from that for:

- targeting work by `work_key`
- targeting runs by `run_id`
- perhaps later supporting human-friendly aliases

without weakening the canonical identity model.

## What We Should Not Take

### 1. Do not collapse work into session

OpenClaw’s identity is for routing conversations and agent runs.

Our identity must remain:

- immutable
- event-sourced
- convergence-bearing

That is a deeper thing than a session key.

### 2. Do not collapse recursive construction into one-shot tasks

The OpenClaw `llm-task` pattern is good for leaf work.

It is not a substitute for:

- recursive graph traversal
- zoom
- spawn
- fold-back
- lawful dynamic refinement

### 3. Do not mistake thread/subagent branching for work decomposition

OpenClaw can branch sessions and subagents.

That is useful.

But our design needs:

- descendants as first-class work
- descendants affecting convergence
- parent collapse as projection over descendants

That is stronger than “spawn another session”.

## The Main Lesson

OpenClaw validates the lower layer of the design:

- hierarchical addressing works
- run identity matters
- lifecycle governance matters
- bounded structured tasks are valuable

But it does not solve the higher layer we care about:

- recursive work
- graph refinement
- convergence law
- event-sourced fold-back

So the right interpretation is:

- OpenClaw is not an alternative model
- it is a proof that some of our lower-level instincts are sound

The most important reusable lessons are:

1. keep hierarchical work identity lawful and readable
2. keep run identity distinct from work identity
3. build stronger run-lifecycle governance around F_P
4. add bounded structured leaf-task primitives where useful
5. keep routing, execution, and work identity separate

## Recommendation

Use OpenClaw as a reference for:

- routing identity
- run lifecycle management
- structured leaf task tooling
- operator ergonomics

Do not use it as the model for:

- convergence
- recursive decomposition
- graph semantics
- fold-back

The correct synthesis is:

- take OpenClaw’s strength at the routing / run-governance layer
- keep ABG/GSDLC’s stronger event-sourced recursive work model
- do not flatten the latter into the former
