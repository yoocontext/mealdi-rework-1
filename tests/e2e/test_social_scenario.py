from typing import cast

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

PASSWORD = "strong-pass-123"


def _register(*, client: TestClient, email: str, name: str) -> dict[str, object]:
    response = client.post(
        "/api/v1/http/auth/register",
        json={"email": email, "name": name, "password": PASSWORD},
    )
    assert response.status_code == 201, response.text

    return cast(dict[str, object], response.json())


def _login(*, client: TestClient, email: str) -> dict[str, object]:
    response = client.post(
        "/api/v1/http/auth/login",
        data={"username": email, "password": PASSWORD},
    )
    assert response.status_code == 200, response.text

    return cast(dict[str, object], response.json())


def _authorization(*, login: dict[str, object]) -> dict[str, str]:
    return {"Authorization": f"Bearer {login['access_token']}"}


def test_refresh_token_is_single_use_and_logout_revokes_replacement(
    *,
    client: TestClient,
) -> None:
    alice = _register(
        client=client,
        email=" Alice@Example.com ",
        name=" Alice ",
    )
    duplicate = client.post(
        "/api/v1/http/auth/register",
        json={
            "email": "alice@example.com",
            "name": "Other Alice",
            "password": PASSWORD,
        },
    )
    bad_login = client.post(
        "/api/v1/http/auth/login",
        data={"username": "alice@example.com", "password": "wrong-password"},
    )

    assert alice["email"] == "alice@example.com"
    assert alice["name"] == "Alice"
    assert duplicate.status_code == 409
    assert bad_login.status_code == 401

    login = _login(client=client, email="ALICE@example.com")
    current = client.get(
        "/api/v1/http/users/me",
        headers=_authorization(login=login),
    )
    assert current.status_code == 200
    assert current.json()["id"] == alice["id"]

    old_refresh = str(login["refresh_token"])
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
    after_logout = client.post(
        "/api/v1/http/auth/refresh",
        json={"refresh_token": new_refresh},
    )
    assert logout.status_code == 200
    assert after_logout.status_code == 401


def test_post_ownership_literal_search_and_unique_like_state(
    *,
    client: TestClient,
) -> None:
    _register(client=client, email="alice@example.com", name="Alice")
    _register(client=client, email="bob@example.com", name="Bob")
    alice_auth = _authorization(
        login=_login(client=client, email="alice@example.com"),
    )
    bob_auth = _authorization(
        login=_login(client=client, email="bob@example.com"),
    )

    created = client.post(
        "/api/v1/http/posts",
        headers=alice_auth,
        json={"content": "A literal 100% _useful_ first post"},
    )
    assert created.status_code == 201, created.text
    post = created.json()

    search = client.get("/api/v1/http/posts", params={"q": "100% _useful_"})
    assert search.status_code == 200
    assert [item["id"] for item in search.json()["items"]] == [post["id"]]

    forbidden_update = client.put(
        f"/api/v1/http/posts/{post['id']}",
        headers=bob_auth,
        json={"content": "stolen"},
    )
    forbidden_delete = client.delete(
        f"/api/v1/http/posts/{post['id']}",
        headers=bob_auth,
    )
    assert forbidden_update.status_code == 403
    assert forbidden_delete.status_code == 403

    liked = client.post(
        f"/api/v1/http/posts/{post['id']}/likes/toggle",
        headers=bob_auth,
    )
    unliked = client.post(
        f"/api/v1/http/posts/{post['id']}/likes/toggle",
        headers=bob_auth,
    )
    assert liked.json() == {"liked": True, "likes_count": 1}
    assert unliked.json() == {"liked": False, "likes_count": 0}


def test_private_conversation_excludes_messages_with_other_users(
    *,
    client: TestClient,
) -> None:
    alice = _register(client=client, email="alice@example.com", name="Alice")
    bob = _register(client=client, email="bob@example.com", name="Bob")
    carol = _register(client=client, email="carol@example.com", name="Carol")
    alice_login = _login(client=client, email="alice@example.com")
    bob_auth = _authorization(login=_login(client=client, email="bob@example.com"))
    carol_auth = _authorization(
        login=_login(client=client, email="carol@example.com"),
    )

    self_message = client.post(
        "/api/v1/http/messages",
        headers=_authorization(login=alice_login),
        json={"recipient_id": alice["id"], "content": "echo"},
    )
    assert self_message.status_code == 403

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            f"/api/v1/http/ws/messages?access_token={alice_login['access_token']}",
            headers={"Origin": "https://attacker.example"},
        ):
            pass

    with client.websocket_connect(
        f"/api/v1/http/ws/messages?access_token={alice_login['access_token']}",
    ) as websocket:
        bob_message = client.post(
            "/api/v1/http/messages",
            headers=bob_auth,
            json={"recipient_id": alice["id"], "content": "from Bob"},
        )
        assert bob_message.status_code == 201, bob_message.text
        assert websocket.receive_json()["data"]["sender_id"] == bob["id"]

        carol_message = client.post(
            "/api/v1/http/messages",
            headers=carol_auth,
            json={"recipient_id": alice["id"], "content": "from Carol"},
        )
        assert carol_message.status_code == 201, carol_message.text
        assert websocket.receive_json()["data"]["sender_id"] == carol["id"]

    conversation = client.get(
        f"/api/v1/http/messages/{bob['id']}",
        headers=_authorization(login=alice_login),
    )
    assert conversation.status_code == 200
    assert [message["content"] for message in conversation.json()["items"]] == [
        "from Bob",
    ]
