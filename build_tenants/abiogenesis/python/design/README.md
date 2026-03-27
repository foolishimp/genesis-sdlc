# Abiogenesis Python Design

**Status**: Draft
**Authority**: [Abiogenesis Python Variant](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/README.md)
**Implements**: `REQ-F-GRAPH-*`, `REQ-F-CMD-*`, `REQ-F-GATE-*`, `REQ-F-TAG-*`, `REQ-F-COV-*`, `REQ-F-DOCS-*`, `REQ-F-TEST-*`, `REQ-F-UAT-*`, `REQ-F-CUSTODY-*`, `REQ-F-TERRITORY-*`, `REQ-F-BOOTDOC-*`, `REQ-F-BACKLOG-*`, `REQ-F-ECO-*`
**Purpose**: ABG and GTL design for the Abiogenesis/Python realization of genesis_sdlc

---

## Scope

`abiogenesis/python` is the concrete variant for the Abiogenesis family.

This surface owns:

- the variant-local module decomposition
- the target source and test boundaries for this realization
- the Python binding choices for package export, evaluator execution, and release surfaces
- the GTL declaration model used by this realization

This surface does not own shared specification truth.

---

## Lifecycle Boundary

This variant realizes the 1.0 base process workflow and its supporting realization surfaces:

- the typed workflow graph
- release bootstrap
- traceability and evidence surfaces
- user-guide and UAT acceptance

This variant also carries the wider ecosystem stages as adjacent lifecycle surfaces:

- `publish`
- `operational_env`
- `monitoring`
- `homeostatic_eval`

These wider ecosystem stages are active requirement truth and sit beside the blocking workflow graph in this realization.

---

## Realization Shape

The Python variant uses this local structure:

- `design/README.md` for variant scope
- `design/module_decomp.md` for the approved module schedule
- `design/modules/*.yml` for per-module build contracts

Concrete implementation surfaces live under this variant, typically as:

- `src/genesis_sdlc/`
- `tests/`
- `release/`

---

## ABG And GTL Encoding

The Python variant encodes the requirement surface as follows:

- lifecycle assets are GTL `Node` declarations
- lifecycle edges are GTL jobs with explicit evaluator sets
- multi-source edges are modeled as `GraphVector` boundaries rather than hidden inside one operator
- the exported package is assembled from multiple GTL `Module` declarations composed into one graph
- evaluator programs run as Python-bound F_D, F_P, or F_H surfaces depending on regime
- optional zoom, profile, consensus, and harvest behavior use `deferred_refinement`, `fan_out`, `fan_in`, and `gate` where the active requirements justify them

The lifecycle truth comes from `specification/requirements/`.

The ABG engine provides `bind_fd()`, `gaps()`, `iterate()`, and `start()` over the exported package.
In this family, the upstream ABG installer provides the engine entry surface, vendored GTL, kernel
bootstrap config seed, and the ABG/GTL bootloader carrier. This variant does not own the ABG
bootloader. It owns the package, evaluator bindings, domain release surfaces, domain bootloader
surfaces, and evidence surfaces that the engine consumes.

---

## Variant Interfaces

The target variant interface set is:

- `instantiate(slug, requirements=None)`
- `package`
- `worker`
- `graph_manifest()`
- `install(target, source, audit_only=False)`
- `load_project_requirements()`
- `render_wrapper()`
- `synthesize_bootloader()`
- `check_tags()`
- `check_req_coverage()`
- `sandbox_e2e_passed()`
- `uat_accepted()`
- `backlog_list()`
- `backlog_promote()`
- `status_with_backlog()`
- `publish()`
- `record_operational_signal()`
- `homeostatic_eval()`

These interfaces are assigned to modules in [module_decomp.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/design/module_decomp.md).

---

## Traceability

- [02-graph.md](/Users/jim/src/apps/genesis_sdlc/specification/requirements/02-graph.md)
- [10-module-decomposition.md](/Users/jim/src/apps/genesis_sdlc/specification/requirements/10-module-decomposition.md)
- [13-bootloader-asset.md](/Users/jim/src/apps/genesis_sdlc/specification/requirements/13-bootloader-asset.md)
- [14-ecosystem-lifecycle.md](/Users/jim/src/apps/genesis_sdlc/specification/requirements/14-ecosystem-lifecycle.md)
