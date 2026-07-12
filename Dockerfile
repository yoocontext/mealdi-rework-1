FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.7.20 /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY alembic.ini ./
COPY migrations ./migrations
COPY src ./src

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app/src

CMD ["uvicorn", "bootstrap.main:app", "--host", "0.0.0.0", "--port", "8000"]
