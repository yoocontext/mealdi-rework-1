# Mealdi Rework

Это rework проекта моего друга Mealdiq. Он сейчас учится разработке, а этот
репозиторий нужен, чтобы помочь ему разобраться в backend-разработке,
архитектуре приложения, тестировании и работе с PostgreSQL.

Mealdi — небольшое социальное приложение с регистрацией и авторизацией,
лентой постов, лайками, профилями пользователей и приватным чатом в реальном
времени через WebSocket.

## Запуск локально

```bash
cp .env.example .env
docker compose up -d postgres
uv sync --all-groups
uv run alembic upgrade head
uv run uvicorn bootstrap.main:app --app-dir src --reload
```

Или можно запустить PostgreSQL и приложение вместе:

```bash
docker compose up --build
```

Документация API доступна по адресу `/docs`, а браузерный клиент — по `/`.

Для production нужно задать случайный `MEALDI_JWT_SECRET`, включить HTTPS и
установить `MEALDI_COOKIE_SECURE=true`.

## Проверки

```bash
uv run ruff check .
uv run mypy src
uv run pytest
uv run alembic check
```
