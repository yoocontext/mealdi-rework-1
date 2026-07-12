import asyncio
import sys
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine
from testcontainers.core import testcontainers_config  # type: ignore[import-untyped]
from testcontainers.postgres import PostgresContainer  # type: ignore[import-untyped]

from bootstrap.main import create_app
from bootstrap.settings import Settings
from infra.orm import Base

POSTGRES_IMAGE = "postgres:18-alpine"


async def _reset_schema(*, database_url: str) -> None:
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()


@pytest.fixture(scope="session")
def postgres_database_url() -> Iterator[str]:
    if sys.platform == "darwin":
        testcontainers_config.ryuk_docker_socket = "/var/run/docker.sock"

    with PostgresContainer(
        image=POSTGRES_IMAGE,
        username="mealdi",
        password="mealdi",
        dbname="mealdi_test",
        driver="asyncpg",
    ) as postgres:
        yield postgres.get_connection_url()


@pytest.fixture
def client(*, postgres_database_url: str) -> Iterator[TestClient]:
    asyncio.run(_reset_schema(database_url=postgres_database_url))
    settings = Settings(
        environment="test",
        database_url=postgres_database_url,
        jwt_secret="test-secret-that-is-long-enough-for-hmac",
        cors_origins=[],
    )

    with TestClient(create_app(settings=settings)) as test_client:
        yield test_client
