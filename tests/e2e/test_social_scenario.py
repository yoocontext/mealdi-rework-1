import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine
from starlette.websockets import WebSocketDisconnect

from bootstrap.main import create_app
from bootstrap.settings import Settings
from infra.common.orm import Base


async def _create_schema(*, database_url: str) -> None:
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()


@pytest.fixture
def client(*, tmp_path: Path) -> TestClient:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'mealdi.sqlite3'}"
    asyncio.run(_create_schema(database_url=database_url))
    settings = Settings(
        environment="test",
        database_url=database_url,
        jwt_secret="test-secret-that-is-long-enough-for-hmac",
        cors_origins=[],
    )

    with TestClient(create_app(settings=settings)) as test_client:
        yield test_client


def _register(
    *,
    client: TestClient,
    email: str,
    name: str,
) -> dict[str, object]:
    response = client.post(
        "/api/v1/http/auth/register",
        json={"email": email, "name": name, "password": "strong-pass-123"},
    )
    assert response.status_code == 201, response.text

    return response.json()


def _login(*, client: TestClient, email: str) -> dict[str, object]:
    response = client.post(
        "/api/v1/http/auth/login",
        data={"username": email, "password": "strong-pass-123"},
    )
    assert response.status_code == 200, response.text

    return response.json()


def _authorization(*, login: dict[str, object]) -> dict[str, str]:
    return {"Authorization": f"Bearer {login['access_token']}"}


def test_complete_social_and_auth_scenario(*, client: TestClient) -> None:
    web = client.get("/")
    assert web.status_code == 200
    assert "mealdi" in web.text

    alice = _register(client=client, email="Alice@Example.com", name="Alice")
    bob = _register(client=client, email="bob@example.com", name="Bob")

    duplicate = client.post(
        "/api/v1/http/auth/register",
        json={
            "email": "alice@example.com",
            "name": "Other Alice",
            "password": "strong-pass-123",
        },
    )
    assert duplicate.status_code == 409

    bad_login = client.post(
        "/api/v1/http/auth/login",
        data={"username": "alice@example.com", "password": "wrong-password"},
    )
    assert bad_login.status_code == 401

    alice_login = _login(client=client, email="alice@example.com")
    bob_login = _login(client=client, email="bob@example.com")
    alice_auth = _authorization(login=alice_login)
    bob_auth = _authorization(login=bob_login)

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            f"/api/v1/http/ws/messages?access_token={alice_login['access_token']}",
            headers={"Origin": "https://attacker.example"},
        ):
            pass

    me = client.get("/api/v1/http/users/me", headers=alice_auth)
    assert me.status_code == 200
    assert me.json()["email"] == "alice@example.com"

    users = client.get("/api/v1/http/users", headers=alice_auth)
    assert users.status_code == 200
    assert [user["id"] for user in users.json()] == [bob["id"]]

    created = client.post(
        "/api/v1/http/posts",
        headers=alice_auth,
        json={"content": "A literal 100% _useful_ first post"},
    )
    assert created.status_code == 201, created.text
    post = created.json()
    assert post["author_name"] == "Alice"
    assert post["likes_count"] == 0

    search = client.get("/api/v1/http/posts", params={"q": "100%"})
    assert search.status_code == 200
    assert [item["id"] for item in search.json()["items"]] == [post["id"]]

    forbidden_update = client.put(
        f"/api/v1/http/posts/{post['id']}",
        headers=bob_auth,
        json={"content": "stolen"},
    )
    assert forbidden_update.status_code == 403

    liked = client.post(
        f"/api/v1/http/posts/{post['id']}/likes/toggle",
        headers=bob_auth,
    )
    assert liked.status_code == 200
    assert liked.json() == {"liked": True, "likes_count": 1}

    unliked = client.post(
        f"/api/v1/http/posts/{post['id']}/likes/toggle",
        headers=bob_auth,
    )
    assert unliked.json() == {"liked": False, "likes_count": 0}

    self_message = client.post(
        "/api/v1/http/messages",
        headers=alice_auth,
        json={"recipient_id": alice["id"], "content": "echo"},
    )
    assert self_message.status_code == 403

    with client.websocket_connect(
        f"/api/v1/http/ws/messages?access_token={alice_login['access_token']}",
    ) as websocket:
        sent = client.post(
            "/api/v1/http/messages",
            headers=bob_auth,
            json={"recipient_id": alice["id"], "content": "hello"},
        )
        assert sent.status_code == 201, sent.text
        event = websocket.receive_json()
        assert event["type"] == "message.created"
        assert event["data"]["sender_id"] == bob["id"]

    conversation = client.get(
        f"/api/v1/http/messages/{bob['id']}",
        headers=alice_auth,
    )
    assert conversation.status_code == 200
    assert [message["content"] for message in conversation.json()["items"]] == [
        "hello",
    ]

    old_refresh = str(alice_login["refresh_token"])
    rotated = client.post(
        "/api/v1/http/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert rotated.status_code == 200, rotated.text
    new_refresh = rotated.json()["refresh_token"]
    assert new_refresh != old_refresh

    replay = client.post(
        "/api/v1/http/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert replay.status_code == 401

    logout = client.post(
        "/api/v1/http/auth/logout",
        json={"refresh_token": new_refresh},
    )
    assert logout.status_code == 200

    after_logout = client.post(
        "/api/v1/http/auth/refresh",
        json={"refresh_token": new_refresh},
    )
    assert after_logout.status_code == 401
