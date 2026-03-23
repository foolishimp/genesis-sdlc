# INSIGHT: GTL Is Dynamic in Principle, Not Yet Compositional in Practice

The key realization is that GTL already behaves like a dynamic system at the package level, but it is still burdensome to extend because the unit of lawful change is too coarse.

Current state:
- `Job` / `Edge` is the executable unit.
- `Package` is the world unit.
- `iterate(job, evaluator_fn, asset)` gives local convergence over one edge.
- `Overlay` gives lawful package extension/restriction.

What is missing is the compositional middle:
- smaller than a `Package`
- larger than a single `Job`
- reusable as a subgraph
- parameterizable by platform, strategy, asset surfaces, and constraints

That missing middle is why GTL feels dynamic but still expensive to evolve:
- extending the workflow means editing/regenerating too much of the graph
- delivery strategy gets hidden inside edge prose or evaluator descriptions
- real DAG structure is hard to express cleanly
- reuse is ad hoc instead of typed and lawful

The likely next abstraction after `gsdlc 1.0` is a first-class workflow fragment / subgraph construct.

Conceptually:
- `Job` = executable transform
- `Fragment` = composable workflow chunk
- `Package` = assembled constitutional world

A fragment should carry:
- boundary inputs
- boundary outputs
- assets
- edges
- jobs
- contexts
- parameterization hooks

Then GTL can grow real composition operators:
- sequential composition
- parallel composition
- specialization / binding
- lawful restriction / profile application
- promotion from fragment to package

This matters because ABG today is effectively a function around an edge. The desired next step is a function around subgraphs.

Practical sequencing:
- do not reopen GTL abstraction before `gsdlc 1.0`
- finish `gsdlc` install/runtime cleanup first
- dogfood the current workflow
- let repeated pain points drive the fragment/subgraph design

Short form:

GTL is already dynamic in principle.
It is not yet dynamically composable in practice.
The missing abstraction is a first-class reusable subgraph / workflow fragment.
