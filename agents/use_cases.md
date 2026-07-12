# Use cases guide

Every use case inherits `BaseUseCase[Cm, Rs]`, uses a keyword-only dataclass for
injected dependencies, and implements `act(*, command)`.

- Commands end in `Cm`, results end in `Rs`, use cases end in `Uc`.
- Dependencies are constructor-injected and `_`-prefixed.
- Use `@dataclass(kw_only=True, slots=True)` and named constructor arguments.
- Only use cases call transaction `commit()`.
- One file contains one use case.
- Mapper paths mirror use-case paths when mapping is non-trivial.
- Make `act()` a short declarative scenario. Extract a named private method for
  a cohesive validation, lookup, or state transition when inline branching
  obscures that scenario. Use a short business comment only when naming and
  whitespace cannot communicate the boundary.
- Translate adapter-specific failures in a small private boundary method; do
  not wrap the whole scenario in `try/except`.

Every use case has a docstring describing its pipeline, persisted changes,
result, and important edge cases.
