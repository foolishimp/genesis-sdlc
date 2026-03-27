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

Two carrier modes are lawful:

- compacted carrier mode: the carrier embeds the compiled bootloader content directly as its operating surface
- paired entry mode: the carrier drives ABG together with the released bootloader artifact, leaving the compiled bootloader as a distinct runtime surface

Both modes preserve the same source/compiled/delivery boundary. The choice between them is a tenant-local design decision unless promoted to common.

In the `abiogenesis` family, paired entry divides ownership as follows:

- the upstream ABG installer provides the engine entry surface, vendored GTL, kernel bootstrap config seed, and the ABG/GTL bootloader carrier
- the domain realization provides package and worker binding, runtime contract, and the domain bootloader artifact or its carrier embedding

The ABG/GTL bootloader remains upstream-owned. Domain packages do not own or rewrite it; they only
add their own compiled domain bootloader surfaces alongside it or through a separate domain carrier.

---

## Consequences

- source truth stays in authored specification and design surfaces
- compiled bootloader drift becomes observable as a graph problem rather than a documentation habit
- control carriers stay replaceable without reclassifying them as constitutional surfaces
- the bootloader may function as the runtime entry surface either by compaction into the carrier or by explicit pairing with ABG
- in the Abiogenesis family, the ABG/GTL bootloader and its carrier originate from the upstream `gen-install.py` boundary and remain upstream-owned
- different realization families or variants may choose different carrier layouts while preserving the same source/compiled/delivery boundary
