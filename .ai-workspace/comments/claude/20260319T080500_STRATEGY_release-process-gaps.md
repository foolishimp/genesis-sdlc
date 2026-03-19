---
Post: STRATEGY
Author: claude
Date: 2026-03-19T08:05:00Z
Subject: Release process gaps — release notes + bootloader versioning
---

# Release Process Gaps — MVP Cleanup

Two gaps identified in `operating-standards/RELEASE.md` during v0.2.0 release cycle.
Both are pre-commit steps. Proposing concrete additions below for author approval.

---

## Gap 1 — No release notes step

### Problem
RELEASE.md has no step for generating a release notes / CHANGELOG entry. Release notes
were produced ad hoc when asked — not as a defined deliverable. This means:
- No canonical record of what changed per version
- Dependent project operators have no upgrade guidance
- The release is traceable in git history but not in human-readable form

### Proposed addition — insert as Step 2b (after version bump, before self-install)

**Step 2b — Write CHANGELOG entry**

Append to `CHANGELOG.md` at the project root:

```markdown
## v{VERSION} — {YYYY-MM-DD}

### Added
- {bullet per new feature/REQ group}

### Changed
- {bullet per modified behaviour}

### Fixed
- {bullet per bug fix}

**REQ keys added**: {comma-separated list or "none"}
**Test results**: {N passed, N skipped, 0 failed}
**Spec hash**: {spec_hash of this release}
```

Rules:
- One entry per release, newest first
- `spec_hash` is the sha256[:16] of `Package.requirements` — lets downstream operators
  know whether their fp_assessment events are still valid after upgrading
- Agent writes the entry; author reviews before commit

---

## Gap 2 — Bootloader not versioned or validated at release

### Problem
`gtl_spec/GENESIS_BOOTLOADER.md` carries an internal version string (`**Version**: 3.0.2`)
but:
- The version is not bumped as part of the release process
- There is no check that the bootloader in the repo matches what's injected into CLAUDE.md
  by the installer
- Downstream projects get a stale bootloader if it changed but install.py wasn't updated
- No traceability between genesis_sdlc release version and bootloader version

### Proposed addition — two changes

**A. Bootloader version pinned in install.py**

Add a constant to `install.py`:

```python
BOOTLOADER_VERSION = "3.0.2"  # matches ** Version**: line in gtl_spec/GENESIS_BOOTLOADER.md
```

Add a validation step to `install()` — warn (not fail) if the bootloader file's internal
version string doesn't match `BOOTLOADER_VERSION`. Prevents silent drift.

**B. New release step — Step 1b (after tests pass, before version bump)**

**Step 1b — Verify and bump bootloader version if changed**

```bash
# Check if bootloader content changed since last release
git diff HEAD~1 gtl_spec/GENESIS_BOOTLOADER.md
```

If changed:
1. Bump the `**Version**:` line in `GENESIS_BOOTLOADER.md` (PATCH for wording,
   MINOR for new sections, MAJOR for removed sections)
2. Update `BOOTLOADER_VERSION` constant in `install.py`
3. Update CHANGELOG entry to note bootloader version

If unchanged: no action needed.

**C. CHANGELOG entry includes bootloader version**

Add `**Bootloader**: v{X.Y.Z}` to the CHANGELOG entry format so operators know which
bootloader their installed project carries.

---

## Proposed RELEASE.md step order (revised)

```
1.   Verify all tests pass
1b.  Verify and bump bootloader version if changed       ← NEW
2.   Bump version (all 5 files)
2b.  Write CHANGELOG entry                               ← NEW
3.   Self-install
4.   Run tests again
5.   Verify gaps converged
6.   Commit
7.   Tag and push
8.   Cascade install to dependent projects
9.   Emit release event (optional)
```

---

## Open questions for author

1. Should CHANGELOG.md be a single file at repo root, or per-platform under `builds/`?
2. Should the bootloader version be independent of the genesis_sdlc version, or should
   a bootloader change always force a genesis_sdlc MINOR bump?
3. Is `spec_hash` in the CHANGELOG useful, or is it too implementation-specific?
