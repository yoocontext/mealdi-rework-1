# Use Cases guide

Every use case inherits `BaseUseCase[Cm, Rs]`, uses `Cm`/`Rs`/`Uc` naming,
aggregates injected dependencies with `@dataclass(kw_only=True, slots=True)`,
and exposes `act(*, command)`.
Only use cases call `commit()`. Data mappers remain persistence-only.

Every use case has a pipeline docstring. Keep one use case per file and put all
business branching here, never in HTTP handlers or data mappers.

Keep `act()` short and declarative. Extract cohesive validation, lookup, and
state-transition steps into business-named private methods when branching would
hide the scenario. Add a short block comment only when names and whitespace are
not enough; do not create one-line indirection or wrap a whole use case in
`try/except`.
