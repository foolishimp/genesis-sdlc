# GAP: Platform Dependency in Traceability Assurance

**Author**: Claude Code
**Date**: 2026-03-16T06:45:00Z
**Addresses**: genesis_sdlc traceability evaluators, `check-tags` engine command, `--platform` installer flag
**For**: all

## Summary

The traceability assurance evaluators in genesis_sdlc are hardcoded to Python. Adding a user guide asset exposed this — `check-tags` only scans `.py` files and only knows `#`-style comment syntax. Any non-Python project installed via genesis_sdlc inherits broken F_D evaluators.

## The Gap

Three layers of hardcoding conflate platform with methodology:

**1. Engine `check-tags` command**
Scans `*.py` only. Tag pattern hardcoded: `# Implements:` / `# Validates:`. A Java or TypeScript project cannot satisfy these evaluators regardless of how it tags its source.

**2. GTL spec evaluator commands**
```python
command="python -m genesis check-tags --type implements --path builds/python/src/"
```
`builds/python/src/` is substituted by the installer `--platform` flag. The tag pattern and file extension are not.

**3. Installer `--platform` substitution**
Replaces build paths (`builds/python/` → `builds/java/`). Does not substitute comment syntax or file extensions in evaluator command strings.

## Constraint Violated

The GTL spec defines assets and their traceability contracts. The engine executes the check generically. The platform binding (comment syntax, file extension) belongs in neither the spec nor the engine — it is a third surface that currently does not exist.

## Proposed Resolution

**Engine**: generalise `check-tags` to accept `--pattern TEXT --ext EXT` instead of `--type`. Existing `--type implements|validates` become aliases over the generic form. One engine change; no future engine changes needed for new asset types or platforms.

**Platform profile**: a first-class concept alongside the GTL Package. Declares `comment_style`, `src_ext`, `test_ext`, `test_runner` for each supported platform. Installer reads the profile and binds evaluator command templates at install time.

**GTL spec**: evaluator commands use template variables (`{src_ext}`, `{comment}`, `{src_path}`) resolved at install time from the platform profile. The spec stays abstract; the platform profile materialises it.

| Platform | `comment` | `src_ext` | `test_runner` |
|----------|-----------|-----------|---------------|
| python | `#` | `.py` | `pytest` |
| java | `//` | `.java` | `mvn test` |
| typescript | `//` | `.ts` | `jest` |
| go | `//` | `.go` | `go test` |
| docs | `<!--` | `.md` | — |

## Scope

This is not a V1 defect — V1 is single-platform (Python). It becomes load-bearing when:
- The user guide asset is added (first `.md` asset requiring `<!-- Covers:` traceability)
- A non-Python project attempts to adopt genesis_sdlc

The user guide addition forces the issue at `covers` tag type. The platform profile is the complete fix; `--pattern/--ext` generalisation is the minimal fix for the immediate user guide case.

## Recommended Action

1. Backlog the platform profile as `BL-001` — not V1 scope, but must precede any multi-platform marketing claim
2. Implement `check-tags --pattern --ext` generalisation in abiogenesis as the immediate fix — unblocks user guide asset without the full platform profile design
3. Update genesis_sdlc evaluator commands to use `--pattern '<!-- Covers:'  --ext .md` for the user guide edge
