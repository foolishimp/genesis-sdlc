# REVIEW: Bootloader split completed — each package appends its own bootloader

**Date**: 2026-03-20
**Supersedes**: 20260320T180000_GAP_bootloader-split-universal-vs-sdlc.md

---

## What changed

The monolithic `GENESIS_BOOTLOADER.md` has been split into two independently-owned bootloaders. Each package in the install chain appends its own bootloader to CLAUDE.md using its own markers.

### Install chain model

```
abg gen-install.py  →  appends GTL_BOOTLOADER.md   between <!-- GTL_BOOTLOADER_START/END -->
gsdlc install.py    →  appends SDLC_BOOTLOADER.md  between <!-- SDLC_BOOTLOADER_START/END -->
```

A future non-SDLC GTL Package (chatbot, data pipeline) would append its own domain bootloader instead of SDLC_BOOTLOADER.md, keeping the GTL bootloader unchanged.

### Files created/modified

**abiogenesis:**
- `builds/claude_code/code/gtl_spec/GTL_BOOTLOADER.md` — universal formal system (I–XI), v1.0.0
- `builds/claude_code/code/gen-install.py` — added `install_claude_md()`, GTL markers, SPEC_FILES updated

**genesis_sdlc:**
- `builds/python/src/genesis_sdlc/SDLC_BOOTLOADER.md` — SDLC instantiation (XII–XX), v1.0.0
- `builds/python/src/genesis_sdlc/install.py` — reads SDLC_BOOTLOADER, uses SDLC markers, migrates legacy GENESIS markers
- `CLAUDE.md` — restructured: GTL block + SDLC block + §XXI project-local
- `builds/python/tests/test_installer.py` — updated marker assertions
- `builds/python/tests/test_e2e_sandbox.py` — updated marker assertion

### Section XXI

Moved to project-local content within CLAUDE.md (inside the SDLC bootloader markers for genesis_sdlc). Not in either shared bootloader file.

### Legacy migration

The gsdlc installer detects `<!-- GENESIS_BOOTLOADER_START -->` markers and removes them during install — the split bootloaders supersede the monolith.

### Test status

All tests pass in both projects (27 abg, 100+ gsdlc).
