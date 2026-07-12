# Application layer guide

See `agents/application.md`.

Application code depends only on its own DTOs, interfaces, services, use cases,
and `application/common`. It must remain runnable without FastAPI or SQLAlchemy.

Every project-owned contract is keyword-only. Use `kw_only=True` for
dataclasses and `*` for function and method parameters.
