# Abiogenesis Python Design

**Status**: Draft
**Authority**: [Abiogenesis Python Variant](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/README.md)
**Implements**: `REQ-F-GRAPH-*`, `REQ-F-CMD-*`, `REQ-F-GATE-*`, `REQ-F-TAG-*`, `REQ-F-COV-*`, `REQ-F-DOCS-*`, `REQ-F-TEST-*`, `REQ-F-UAT-*`, `REQ-F-CUSTODY-*`, `REQ-F-TERRITORY-*`, `REQ-F-BOOTDOC-*`, `REQ-F-BACKLOG-*`, `REQ-F-ECO-*`, `REQ-F-MVP-*`, `REQ-F-ASSURE-*`, `REQ-F-CTRL-*`, `REQ-F-WORKER-*`
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

These wider ecosystem stages are active requirement truth and sit beside the blocking workflow graph in this realization, but `backlog_homeostasis` remains outside the active `0.9.9` refactor wave.

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

Variant-local design decisions that are stable enough to ratify sit under `design/adrs/`.

---

## ABG And GTL Encoding

The Python variant encodes the requirement surface as follows:

- lifecycle assets are GTL `Node` declarations
- lifecycle edges are GTL jobs with explicit evaluator sets
- lifecycle jobs expose generic workflow roles as constitutional execution law
- multi-source edges are modeled as `GraphVector` boundaries rather than hidden inside one operator
- the exported package is assembled from multiple GTL `Module` declarations composed into one graph
- the exported `worker` surface is a runtime dispatch/router boundary rather than a hidden singleton vendor worker
- evaluator programs run as Python-bound F_D, F_P, or F_H surfaces depending on regime
- optional zoom, profile, consensus, and harvest behavior use `deferred_refinement`, `fan_out`, `fan_in`, and `gate` where the active requirements justify them
- the assurance control plane compiles release defaults, tenant-local `build_tenants/<techlabel>/design/fp/` tuning, and runtime state into one resolved runtime artifact
- `release_bootstrap` publishes the install-managed runtime carrier under `.gsdlc/release/runtime/`, including backend and worker registry defaults, while `assurance_control_plane` owns the schemas, worker-assignment rules, adapter contract, and operative consumers inside that carrier
- backend adapters belong to the control plane, not to graph law
- backend identity is derived from the winning worker assignment rather than resolved as a co-equal selector
- for `0.9.9`, declared workers assume their bound vendor CLI is already installed and authenticated; the variant standardizes invocation and evidence, not backend provisioning
- any rendered F_P prompt is a read model derived from the resolved runtime, not a separate operative path

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
- `compile_resolved_runtime()`
- `load_resolved_runtime()`
- `load_worker_registry()`
- `resolve_worker_assignments()`
- `invoke_worker_turn(role, prompt, work_folder, timeout)`
- `load_backend_registry()`
- `probe_backends()`
- `normalize_backend_result(raw_result, backend)`
- `describe_backend_failure(raw_failure, backend)`
- `backend_capabilities(backend)`
- `doctor()`
- `render_effective_prompt(manifest_path)`
- `check_tags()`
- `check_req_coverage()` (deferred in the current `1.0` line)
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

## Assurance Model

This variant carries a bundled assurance surface alongside the workflow itself.

The assurance model preserves two provenance paths:

- the design realization path: `design -> module_decomp -> code` and `design -> module_decomp -> unit_tests`
- the requirements-facing acceptance path: `requirements -> integration_tests -> user_guide -> uat_tests`

`integration_tests` is the join between those paths. It proves that the realized code and tests behave as required in one runnable scenario. `user_guide` and `uat_tests` then close the operator-facing release path against the active requirement surface.

The bundled assurance surface lives under `tests/` and provides:

- fake-lane qualification for workflow law
- live-lane qualification for real F_P execution
- persistent run archives for postmortem and operator review

Both product commands and qualification consume the same resolved runtime and backend adapter layer. The assurance harness is not allowed to remain a separate operative transport path once the control plane exists.

Run archives must preserve engine build identity, assigned worker identity, and transport backend identity as distinct provenance surfaces. The variant does not collapse those three layers into one field.

This variant therefore treats qualification as part of the framework realization, not as an external demo harness.

---

## Variant ADRs

- [ADR-001-gtl-python-coding-standards.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/design/adrs/ADR-001-gtl-python-coding-standards.md)
- [ADR-002-assurance-control-plane.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/design/adrs/ADR-002-assurance-control-plane.md)

---

## Traceability

- [02-graph.md](/Users/jim/src/apps/genesis_sdlc/specification/requirements/02-graph.md)
- [10-module-decomposition.md](/Users/jim/src/apps/genesis_sdlc/specification/requirements/10-module-decomposition.md)
- [13-bootloader-asset.md](/Users/jim/src/apps/genesis_sdlc/specification/requirements/13-bootloader-asset.md)
- [14-ecosystem-lifecycle.md](/Users/jim/src/apps/genesis_sdlc/specification/requirements/14-ecosystem-lifecycle.md)
- [15-mvp.md](/Users/jim/src/apps/genesis_sdlc/specification/requirements/15-mvp.md)
- [16-assurance.md](/Users/jim/src/apps/genesis_sdlc/specification/requirements/16-assurance.md)
- [17-control-plane.md](/Users/jim/src/apps/genesis_sdlc/specification/requirements/17-control-plane.md)
- [18-workers.md](/Users/jim/src/apps/genesis_sdlc/specification/requirements/18-workers.md)
