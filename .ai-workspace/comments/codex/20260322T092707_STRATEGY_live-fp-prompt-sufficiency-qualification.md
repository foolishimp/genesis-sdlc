# STRATEGY: Live F_P Prompt Sufficiency Qualification

**Date**: 2026-03-22T09:27:07Z  
**Status**: Proposed  
**Applies to**: `abg 1.0` release evidence

## Purpose

The current judged scenario suite proves:

- the ABG F_P protocol is real
- `iterate -> manifest -> result_path -> assess-result -> gaps` is real
- deterministic judges can distinguish acceptable from unacceptable artifacts

It does **not** yet prove the thing that matters for release:

> the actual F_P dispatch payload produced by ABG is sufficient for a real LLM to generate an acceptable artifact within tolerance

That is a different test.

## Core Question

The release question is not only:

- does the protocol work?

It is:

- given the real prompt/manifest ABG produces, can a real LLM respond in a way we would accept often enough to trust the system?

## Required Test Shape

Add a **live F_P qualification lane**.

For a live qualification run:

1. Set up the sandbox and explicit package as normal.
2. Run `genesis iterate`.
3. Capture the real `fp_manifest_path`.
4. Invoke a real LLM using exactly the F_P dispatch contract ABG guarantees.
5. Require the LLM to:
   - produce the target artifact
   - write the `result_path` assessment file
6. Run `genesis assess-result`.
7. Run `genesis gaps`.
8. Run the deterministic judge as an independent cross-check.

## Critical Rule

If the goal is to validate prompt sufficiency, the LLM must receive **only** what production guarantees.

That means this must be explicit:

- if production contract is `manifest JSON only`, test with manifest JSON only
- if production contract is `manifest prompt + CLAUDE.md`, test with exactly that

Do not allow hidden side channels in the qualification run, or the test will not answer the real question.

## Success Criterion

Do not require a single perfect run. This is a probabilistic system.

Treat qualification as a success-rate test:

- same scenario
- same model
- same transport
- same config
- multiple runs
- deterministic judge over the resulting artifact

Suggested starting bar:

- `requirements -> uat_tests`: 10 runs, require at least 8/10 judged acceptable
- `design -> data_schema`: 10 runs, require at least 8/10 judged acceptable

No manual repair.
No hidden retries unless retries are part of the shipped behavior.

## First Scenarios

Start with only two:

1. `requirements -> uat_tests`
   - highest release value
   - clear deterministic judge
   - strongest evidence for shipping usefulness

2. `design -> data_schema`
   - structured constraints
   - good at exposing prompt/context insufficiency

Do **not** start with code generation.

## Why This Matters

This test answers the real release question:

- protocol real? yes
- prompt sufficient? unknown until qualified live

Without this, ABG can truthfully claim:

- the protocol is real

but cannot yet truthfully claim:

- the shipping F_P prompt surface is good enough for a real LLM within tolerance

## Archive Requirements

Every live qualification run should archive:

- manifest JSON
- exact prompt payload sent
- model/config used
- raw LLM output or transcript
- produced artifact
- written result file
- assessed events
- final gaps result
- deterministic judge verdict

The archive must allow a reviewer to answer:

- what did ABG send?
- what did the LLM return?
- why was it accepted or rejected?

## Release Use

This should become explicit release evidence.

A clean `abg 1.0` claim is then:

- the protocol works
- the archive is trustworthy
- the prompt/manifest surface has been live-qualified against a real LLM within tolerance

That is the correct bar if the system is supposed to drive real F_P behavior in production.
