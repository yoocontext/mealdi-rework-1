# Data mapper guide

Data mappers implement application persistence ports.

- A data mapper receives `TransactionManager`, never raw `AsyncSession`.
- A data mapper never commits or rolls back; it may add, delete, flush, refresh,
  and execute persistence queries through the transaction manager.
- Keep SQL and SQLAlchemy inside `infra/dm`.
- Mapping details live in `infra/dm/mappers/`.
- Split files by aggregate or stable business concept.
- Return application DTOs, never ORM instances.
- Keep data-mapper method contracts keyword-only and use named calls.
- Persistence failures follow `AppError → InfraError → DmError → concrete
  error`; use typed fields and a `message` property instead of `RuntimeError`.
