# Data Mapper guide

Data mappers implement application persistence interfaces and contain only
simple persistence operations such as `get`, `list`, `create`, `save`, and
`delete`.

- Inject `TransactionManager`; raw `AsyncSession` is forbidden in data mappers.
- `commit()` is forbidden; use cases own transaction boundaries.
- Business decisions and authorization are forbidden.
- ORM-to-application mapping belongs in `infra/dm/mappers/`.
- Split implementations and mappers by stable business concept.
- Keep method contracts keyword-only and call them with named arguments.
- Raise concrete `DmError` subclasses with typed context for persistence
  invariants; never raise an ad-hoc `RuntimeError`.
