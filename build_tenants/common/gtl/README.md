# Common GTL

**Status**: Ratified
**Purpose**: Portable GTL definition layer shared across realization families

---

## Scope

`build_tenants/common/gtl/` holds GTL-level definitions, contracts, and precedents intended to remain portable across realization families and variants.

It is the correct home for:

- portable graph-definition law
- GTL-level contracts shared across tenants
- common precedents that should survive family or variant changes

It is not a build_tenant and not a binding surface.

---

## Boundary

If a GTL definition or rule is intended to remain valid across `abiogenesis`, `temporal`, `bedrock`, or other future realization families, it belongs here rather than inside one family surface.
