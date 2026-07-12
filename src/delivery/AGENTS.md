# Delivery layer guide

Versioned transports live under `delivery/v{version}/{transport}/`.

- `handlers/` is split by resource.
- `schemas/` owns request and response validation.
- `mappers/` converts transport values to commands and results to responses.
- `exceptions.py` maps expected application failures to HTTP responses.

Handlers do transport orchestration only. They never access SQLAlchemy or apply
business authorization rules.

Keep handlers linear. Put exception translation and connection lifecycle in
small named boundary functions or context managers.

Project-owned handlers and mappers use keyword-only parameters and named calls.
