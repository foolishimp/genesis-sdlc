# Release Process Conventions

**Governance**: Maintained by the methodology author. Read-only for agents.

**NOTE TO LLM**: If this file is referenced in a prompt, it is an active instruction to execute a release following this process exactly. Do not skip steps. Do not reorder steps.

---

## Version Numbering

```
MAJOR.MINOR.PATCH
```

| Increment | When |
|-----------|------|
| `PATCH` | Bug fix — no new REQ keys, no interface changes, no new commands |
| `MINOR` | New feature — new REQ keys, new commands, new public behaviour. Backward compatible. |
| `MAJOR` | Breaking change — removed commands, changed interfaces, incompatible workspace format |

**Rule**: Adding REQ keys is always at least a MINOR bump. The spec_hash changes, which invalidates all prior fp_assessment events in dependent projects — that is a breaking change to the convergence state.

---

## Files to Update on Every Release

Update ALL of these atomically — a partial version bump is a defect:

| File | Field |
|------|-------|
| `builds/python/src/genesis_sdlc/install.py` | `VERSION = "x.y.z"` |
| `builds/python/src/genesis_sdlc/__init__.py` | `__version__ = "x.y.z"` |
| `builds/python/pyproject.toml` | `version = "x.y.z"` |
| `builds/python/tests/test_sdlc_graph.py` | `assert genesis_sdlc.__version__ == "x.y.z"` |
| `builds/python/tests/test_installer.py` | `assert data["version"] == "x.y.z"` |

---

## Release Steps

### 1. Verify all tests pass

```bash
PYTHONPATH=builds/python/src:.genesis python -m pytest builds/python/tests/ -m 'not e2e'
```

All must pass. Do not proceed with failures.

### 2. Bump version

Update all files in the table above to the new version string.

### 3. Self-install

```bash
PYTHONPATH=builds/python/src:.genesis python -m genesis_sdlc.install \
  --target . \
  --project-slug genesis_sdlc
```

This updates `.claude/commands/`, `CLAUDE.md` (bootloader), and `.ai-workspace/operating-standards/`.

### 4. Run tests again

Verify the self-install did not break anything:

```bash
PYTHONPATH=builds/python/src:.genesis python -m pytest builds/python/tests/ -m 'not e2e'
```

### 5. Verify gaps converged

```bash
PYTHONPATH=.genesis python -m genesis gaps --workspace .
```

`converged: true` required. If not, the release has introduced a spec change that invalidates prior assessments — drive to convergence before releasing.

### 6. Commit

```bash
git add -A
git commit -m "feat(v{VERSION}): {short description of what changed}"
```

Commit message format: `feat` for new features, `fix` for bug fixes, `chore` for tooling/process changes.

### 7. Tag and push

```bash
git tag v{VERSION}
git push origin main --tags
```

### 8. Cascade install to dependent projects

For each project that depends on genesis_sdlc, run the installer:

```bash
PYTHONPATH=builds/python/src:.genesis python -m genesis_sdlc.install \
  --target /path/to/dependent/project \
  --project-slug {slug}
```

Commit the updated artifacts in the dependent project:

```bash
cd /path/to/dependent/project
git add .claude/ .genesis/ CLAUDE.md .ai-workspace/operating-standards/
git commit -m "chore: cascade genesis_sdlc v{VERSION}"
git push origin main
```

### 9. Emit release event (optional)

If the workspace event log is active:

```bash
PYTHONPATH=.genesis python -m genesis emit-event \
  --type genesis_sdlc_released \
  --data '{"version": "{VERSION}", "summary": "{short description}"}'
```

---

## Known Dependent Projects

Update this list when new projects adopt genesis_sdlc:

- `genesis-manager` — `--project-slug genesis_manager`

---

## What Does Not Need a Release

- Editing `standards/` files (operating standards) — update the source, re-run self-install, commit
- Editing comment posts in `.ai-workspace/comments/` — these are workspace artifacts, not versioned artifacts
- Editing ADRs in `builds/python/design/adrs/` — ADRs are immutable; supersede with a new ADR
