# Mealdi

Mealdi is a small social network with accounts, refresh-token authentication,
a searchable post feed, unique likes, user profiles, and private chat with live
WebSocket delivery. This repository is a clean rewrite of `mildinet`.

The browser client is available at `/`, OpenAPI at `/docs`, and every public
API endpoint is under `/api/v1/http`.

## Mental model

Every request follows one direction:

```text
HTTP/WebSocket handler
  → one application use case
    → narrow application interfaces
      → SQLAlchemy/security implementation
```

Only the use case commits. Handlers never see ORM objects, data mappers never
decide permissions, and infrastructure does not import delivery. `bootstrap/` is the
only place that assembles concrete objects.

Use cases read as short declarative scenarios; cohesive validations and state
transitions have business-named private methods. Expected failures form one
typed hierarchy (`AppError` → layer → component → concrete error) and own their
safe public message. Infrastructure data mappers work through a request-scoped
`TransactionManager`, so raw `AsyncSession` never leaks past `infra/common` and
the composition root.

```text
src/
  bootstrap/                 # settings, IoC, process entrypoint, layer common
  application/
    common/                  # application-only base types and errors
    dto/                     # persistence-independent data
    interfaces/              # database, security, clock, transaction ports
    use_cases/{auth,users,posts,messages}/
  delivery/
    common/                  # transport-owned connection/settings types
    api/v1/http/
      handlers/              # one transport action per endpoint
      schemas/               # request/response validation
      mappers/               # application ↔ HTTP mapping
    web/                     # dependency-free browser client
  infra/
    common/                  # SQLAlchemy base, clock, transaction
    dm/                      # data mapper implementations and mappers
    orm/                     # persistence models only
    security/                # Argon2 and JWT implementations
```

There are deliberately no `modules/` and no `seedwork/`. Shared abstractions
live in the `common/` of the layer that owns them.

## Important corrections from the original

- refresh tokens are returned, stored only as HMAC digests, rotated under a
  database lock, and actually revoked by logout;
- access tokens validate type, issuer, audience, expiry, and subject;
- WebSocket identity comes from a signed token/cookie, never a user id in the
  path, and cross-origin handshakes are rejected;
- sender and author identity always comes from authentication;
- post ownership is an application rule with explicit 403/404 outcomes;
- likes use a composite primary key and a derived count, so counters cannot
  drift; concurrent toggles serialize on the post;
- posts have a real author foreign key and all dependent rows have database
  cascades;
- search correctly treats `%` and `_` as literal input and pagination is
  bounded;
- route ordering cannot make `/users/me` disappear behind `/{user_id}`;
- transactions and rollback lifecycle are centralized in request-scoped IoC.

## Run locally

```bash
cp .env.example .env
docker compose up -d postgres
uv sync --all-groups
uv run alembic upgrade head
uv run uvicorn bootstrap.main:app --app-dir src --reload
```

Or start both PostgreSQL and the application:

```bash
docker compose up --build
```

Production must set a random `MEALDI_JWT_SECRET`, use HTTPS, and set
`MEALDI_COOKIE_SECURE=true`.

## Checks

```bash
uv run ruff check .
uv run mypy src
uv run pytest
uv run alembic check
```

The test suite includes architecture boundaries and a full scenario through
HTTP, WebSocket, SQLAlchemy, token rotation, permissions, search, likes, and
message history.
