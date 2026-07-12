# Application layer guide

## Structure

- `use_cases` — one business scenario per file.
- `interfaces` — ports implemented by infrastructure.
- `dto` — transport- and persistence-independent business data.
- `services` — reusable business policies used by multiple scenarios.
- `common` — application-only base abstractions and errors.

One component has one focused interface. Application code must not import
FastAPI, SQLAlchemy, or infrastructure implementations.

All application contracts are keyword-only: dataclasses use `kw_only=True`,
methods place `*` after `self`, and callers always name arguments explicitly.

Application errors derive from `AppError → ApplicationError → category →
concrete error`. Concrete errors carry typed context and own their public
`message`; raise sites do not assemble ad-hoc error strings.
