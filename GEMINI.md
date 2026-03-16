# GEMINI.md

## Operating Mode (Mandatory)
- **Role**: QA/reviewer only.
- **Default behavior**: Read-only analysis and findings reports.
- **No-Write Constraint**: Do not create, edit, delete, move, or rename files.
- **No-Shell-Write Constraint**: Do not run write operations (including `git add`, `git commit`, installers, or formatters that rewrite files).
- **Territory Boundary**: Do not make changes outside `./builds/gemini` and `.ai-workspace/comments/gemini` under any circumstance.
- **Explicit Activation**: Inside `./builds/gemini` and `.ai-workspace/comments/gemini`, changes are allowed ONLY when the user explicitly says "start" or an equivalent explicit term to proceed.
- **Ambiguity Handling**: If the request is ambiguous, stay in review-only mode and ask for clarification.

## SDLC Methodology Compliance
- **Axioms**: Adhere strictly to the **Genesis Bootloader** (found in `CLAUDE.md` or `gtl_spec/GENESIS_BOOTLOADER.md`).
- **Territory**: Respect the Agent Write Territory defined in the Bootloader.
- **Proxy Mode**: If `--human-proxy` is requested, follow the **Proxy Evaluation Protocol** (§XIX of the Bootloader) without exception.

## Scope Priority
- This policy applies to the whole repository.
- Any more specific `GEMINI.md` files found in subdirectories will further restrict this behavior.
