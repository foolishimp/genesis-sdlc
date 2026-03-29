# Common Qualification

**Status**: Active
**Purpose**: Shared qualification law and classification surfaces for genesis_sdlc realizations

---

## Scope

`build_tenants/common/qualification/` is the shared root for cross-tenant qualification law.

It contains:

- shared qualification boundary and classification surfaces
- maps that explain what is tenant-local versus genuinely shared
- method-facing guidance for how executable test roots relate to module ownership

Executable tests do not become shared merely because one tenant already has them.

Promotion into `common/qualification/` is explicit.
