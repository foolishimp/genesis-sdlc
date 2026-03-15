# Release Process — genesis_sdlc

See also: `abiogenesis/builds/claude_code/code/RELEASE.md` for the full cascade description.

## Source of Truth

| Artifact | Source | Derived (do not edit directly) |
|----------|--------|-------------------------------|
| gen-iterate, gen-review | `builds/claude_code/.claude-plugin/plugins/genesis/commands/` | `.claude/commands/` |
| gen-start, gen-gaps, gen-status | `abiogenesis/builds/claude_code/.claude-plugin/plugins/genesis/commands/` | `.claude/commands/` |
| install.py | `builds/python/src/genesis_sdlc/install.py` | — |
| Engine | `abiogenesis/builds/python/src/` | `.genesis/genesis/`, `.genesis/gtl/` |

## Fix → Release → Install Cascade

### Bug in genesis_sdlc (gen-iterate or gen-review)

1. Fix source in `builds/claude_code/.claude-plugin/plugins/genesis/commands/`

2. Bump version in **both**:
   - `builds/python/src/genesis_sdlc/install.py` → `VERSION = "0.1.x"`
   - `builds/python/pyproject.toml` → `version = "0.1.x"`

3. Commit source changes

4. Self-install:
   ```bash
   python builds/python/src/genesis_sdlc/install.py \
     --target . \
     --project-slug genesis_sdlc
   ```

5. Commit installed artifacts (`.claude/commands/`, stamp file)

### Bug in abiogenesis (gen-start, gen-gaps, gen-status or engine)

Fix in abiogenesis first, then run genesis_sdlc installer against both projects.
See `abiogenesis/builds/claude_code/code/RELEASE.md` for the full procedure.

## Installer Reads Commands From

```python
ABIOGENESIS_COMMANDS = ["gen-start", "gen-gaps", "gen-status"]
# source: ../abiogenesis/builds/claude_code/.claude-plugin/plugins/genesis/commands/

GENESIS_SDLC_COMMANDS = ["gen-iterate", "gen-review"]
# source: builds/claude_code/.claude-plugin/plugins/genesis/commands/
```
