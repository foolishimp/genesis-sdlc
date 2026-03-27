# ADR-002 — Bootloader And Control Carriers

**Status**: Approved
**Date**: 2026-03-27
**Implements**: REQ-F-BOOT-*, REQ-F-BOOTDOC-*

---

## Context

The specification now distinguishes three things that were previously blurred:

- authored source documents
- the compiled bootloader artifact
- the concrete agent entry/control carriers that deliver orientation into a runtime

Without a shared design decision, carrier files are likely to be mistaken for primary source, and compiled output is likely to drift back into hand-maintained doctrine.

---

## Decision

genesis_sdlc adopts the following boundary:

- specification and design documents remain authored source surfaces
- the bootloader is a compiled graph asset derived from those source surfaces
- control carriers are delivery surfaces chosen by design

Control carriers may embed or cache bare operating axioms, but they are not primary source. Their role is to orient the runtime and route it back to canonical process and design documents.

Concrete carrier filenames, placement, and embedding topology remain design choices below this shared boundary.

---

## Consequences

- source truth stays in authored specification and design surfaces
- compiled bootloader drift becomes observable as a graph problem rather than a documentation habit
- control carriers stay replaceable without reclassifying them as constitutional surfaces
- different realization families or variants may choose different carrier layouts while preserving the same source/compiled/delivery boundary
