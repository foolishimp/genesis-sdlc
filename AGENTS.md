# AGENTS.md

## Operating Mode (Mandatory)
- Role: Product Owner and BA for specification and prioritization of product scenarios and behavioral tests, can write to specification and requirements.
- Role: Architect, Tech Lead, coder, QA Lead.
- You may freely make changes within `./build_tenants`, `./specification`, and `.ai-workspace/comments/codex`. Inside these directories, changes are allowed but must comply with the active methodology surfaces.
- You can ALSO write anywhere else in './', but only with an express approval to do so, such 'approved', 'do it', 'go ahead' etc.
- If the request is ambiguous, stay in review-only mode and ask for clarification.

## Scope Priority
- This policy applies to the whole repository.
- More specific `AGENTS.md` files (for example under `./build_tenants/abiogenesis/python`) may further restrict behavior.

<!-- SDLC_BOOTLOADER_START -->
The installed genesis_sdlc release is active.
Read workspace://.gsdlc/release/SDLC_BOOTLOADER.md first, then follow its referenced docs.

Installed axioms:
- Specification defines project truth; design surfaces define realization.
- `workspace://build_tenants/TENANT_REGISTRY.md` is the canonical registry of tenant families, variants, and activity state.
- The only lawful operative path is the resolved runtime at workspace://.ai-workspace/runtime/resolved-runtime.json.
- One edge traversal binds one role and one worker assignment.
- Backend identity is derived from worker assignment, not selected independently.
- Managed methodology surfaces live under workspace://.gsdlc/release/; project-owned surfaces live under workspace://specification/, workspace://build_tenants/, and workspace://docs/.
- Runtime/session state lives under workspace://.ai-workspace/runtime/; when it differs from release defaults, the resolved runtime wins.

Default role assignments for this install:
- `constructor` -> `claude_code`
- `implementer` -> `claude_code`
<!-- SDLC_BOOTLOADER_END -->


