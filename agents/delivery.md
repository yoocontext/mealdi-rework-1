# Delivery layer guide

HTTP code lives under `delivery/api/v{version}/http/`.

- `handlers/` contains endpoints grouped by resource.
- `schemas/` contains request and response models with matching names.
- `mappers/` maps schemas to commands and results to responses.
- `dependencies/` contains transport authentication and request extraction.
- `exceptions.py` is the single mapping from project errors to HTTP.

Handlers coordinate transport concerns only. They do not query databases,
perform business decisions, or return ORM objects.

Project-owned handlers and mappers use keyword-only parameters and explicit
named calls. Framework callbacks are exempt only when positional invocation is
required by the framework.

Keep handlers linear. Hide authentication translation, disconnect loops, and
connection cleanup behind narrowly named transport functions/context managers.
