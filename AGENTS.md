# Project architecture

- `bootstrap` — application assembly, settings, dependency wiring, and entrypoint.
- `delivery` — transports: handlers, schemas, mappers, validation, auth.
- `application` — use cases, business data, policies, and ports.
- `infra` — database and security implementations.

There is deliberately no `modules/` or `seedwork/` directory. Shared code is
owned by `common/` inside the layer that uses it.

## Layer dependencies

- `bootstrap` may know every layer.
- `delivery` may know only `application` and `delivery/common`.
- `application` may know only `application/common`.
- `infra` may know application contracts and `infra/common`.

### Import rule

Import only the layers listed above. Never expose ORM objects outside `infra`.

## `src/bootstrap`

- This is the composition root and process entrypoint.
- Register every dependency in `bootstrap/ioc/`.
- Do not instantiate implementations outside IoC providers.

## File and folder granularity

Prefer small files grouped by stable business concept. Refactor ownership as
the domain evolves; do not preserve a poor file structure for compatibility.

Do not create `helpers` or `utils` modules. Put a shared abstraction in the
owning layer's `common/`, and name it after what it does.

## Code rules

- Use dataclasses for application data and dependency aggregation.
- Make dataclasses keyword-only with `@dataclass(kw_only=True, ...)`.
- Make project-owned function and method parameters keyword-only with `*`.
- Call project-owned classes and functions with explicit argument names.
- Constructor-inject every dependency and prefix dependency fields with `_`.
- Keep transport types out of application and infrastructure.
- Keep SQLAlchemy types and queries inside infrastructure.
- Source configuration from settings and environment variables.
- Use timezone-aware UTC timestamps.
- Only use cases commit transactions; data mappers may only flush.
- All expected failures inherit `AppError` and expose a safe `message` property.
- Extend errors by ownership: project → layer → component → concrete failure.
- Keep `try/except` at translation and lifecycle boundaries; move it out of the
  main scenario when a named method can express the boundary.
- Infrastructure data mappers depend on `TransactionManager`, never directly
  on `AsyncSession`.

## Code formatting

Format by semantic blocks. Keep one idea per block and separate setup, query,
execution, branching, mapping, side effects, and return with blank lines.
