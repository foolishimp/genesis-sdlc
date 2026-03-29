# Genesis SDLC User Guide

Version: 1.0rc1

## Installation

Install the ABG kernel first, then install the genesis_sdlc release into the target workspace.
Use `genesis start` (`gen-start`), `genesis iterate` (`gen-iterate`), and `genesis gaps` (`gen-gaps`)
from the installed workspace.

## First Session

Raise or inspect intent, run `genesis gaps`, and review the current delta before iterating the next
edge. Treat the event stream as the durable record of approvals, assessed results, and convergence
state.

## Operating Loop

`F_D` closes deterministic checks, `F_P` performs bounded construction or assessment, and `F_H`
approves release-critical gates. Delta falls as each blocking edge is satisfied; keep iterating until
the required release edges are closed.

## Recovery

If `fd_gap` appears, repair the deterministic surface and rerun gap analysis. If `fp_dispatch`
appears, complete the bounded construction or assessment and submit the result. If an `fh_gate`
appears, perform the required review and approval. Re-run `genesis gaps` after each recovery step.

## Requirement Tags

- REQ-F-BOOT-001
- REQ-F-BOOT-002
- REQ-F-BOOT-003
- REQ-F-BOOT-004
- REQ-F-BOOT-005
- REQ-F-BOOT-006
- REQ-F-BOOT-007
- REQ-F-BOOT-008
- REQ-F-BOOT-009
- REQ-F-BOOT-010
- REQ-F-BOOT-011
- REQ-F-GRAPH-001
- REQ-F-GRAPH-002
- REQ-F-GRAPH-003
- REQ-F-CMD-001
- REQ-F-CMD-002
- REQ-F-CMD-003
- REQ-F-CMD-004
- REQ-F-GATE-001
- REQ-F-TAG-001
- REQ-F-TAG-002
- REQ-F-COV-001
- REQ-F-DOCS-001
- REQ-F-DOCS-002
- REQ-F-TEST-001
- REQ-F-TEST-002
- REQ-F-TEST-003
- REQ-F-TEST-004
- REQ-F-TEST-005
- REQ-F-UAT-001
- REQ-F-UAT-002
- REQ-F-UAT-003
- REQ-F-BACKLOG-001
- REQ-F-BACKLOG-002
- REQ-F-BACKLOG-003
- REQ-F-BACKLOG-004
- REQ-F-MDECOMP-001
- REQ-F-MDECOMP-002
- REQ-F-MDECOMP-003
- REQ-F-MDECOMP-004
- REQ-F-MDECOMP-005
- REQ-F-CUSTODY-001
- REQ-F-CUSTODY-002
- REQ-F-CUSTODY-003
- REQ-F-TERRITORY-001
- REQ-F-TERRITORY-002
- REQ-F-TERRITORY-003
- REQ-F-TERRITORY-004
- REQ-F-BOOTDOC-001
- REQ-F-BOOTDOC-002
- REQ-F-BOOTDOC-003
- REQ-F-BOOTDOC-004
- REQ-F-ECO-001
- REQ-F-ECO-002
- REQ-F-ECO-003
- REQ-F-ECO-004
- REQ-F-MVP-001
- REQ-F-MVP-002
- REQ-F-MVP-003
- REQ-F-ASSURE-001
- REQ-F-ASSURE-002
- REQ-F-ASSURE-003
- REQ-F-CTRL-001
- REQ-F-CTRL-002
- REQ-F-CTRL-003
- REQ-F-CTRL-004
- REQ-F-CTRL-005
- REQ-F-CTRL-006
- REQ-F-CTRL-007
- REQ-F-CTRL-008
- REQ-F-WORKER-001
- REQ-F-WORKER-002
- REQ-F-WORKER-003
- REQ-F-WORKER-004
- REQ-F-WORKER-005
