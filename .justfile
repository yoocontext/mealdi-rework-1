set dotenv-load := true

sync:
    uv sync --all-groups

fmt:
    uv run ruff check . --fix
    uv run ruff format .

check:
    uv run ruff check .
    uv run mypy src
    uv run pytest

migrate:
    uv run alembic upgrade head

app:
    uv run uvicorn bootstrap.main:app --app-dir src --reload

up:
    docker compose up --build
