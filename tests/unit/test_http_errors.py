from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from application.common.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
)
from delivery.api.v1.http.exceptions import install_application_error_handlers
from delivery.api.v1.http.request_id import install_request_id_middleware
from infra.dm.exceptions import SerializationError


def _client() -> TestClient:
    app = FastAPI()
    install_request_id_middleware(app=app)
    install_application_error_handlers(app=app)

    @app.get("/conflict")
    async def conflict() -> None:
        raise EmailAlreadyExistsError()

    @app.get("/authentication")
    async def authentication() -> None:
        raise InvalidCredentialsError()

    @app.get("/infrastructure")
    async def infrastructure() -> None:
        raise SerializationError(
            entity="user",
            identifier="private-id",
            operation="reload",
        )

    @app.get("/http")
    async def http_error() -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found",
        )

    @app.post("/validation")
    async def validation(*, value: int) -> None:
        return None

    @app.get("/unexpected")
    async def unexpected() -> None:
        raise RuntimeError("database password")

    return TestClient(app, raise_server_exceptions=False)


def test_application_error_has_stable_envelope_and_request_id() -> None:
    response = _client().get("/conflict", headers={"X-Request-ID": "test-123"})

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.headers["X-Request-ID"] == "test-123"
    assert response.json() == {
        "error": {
            "code": "email_already_exists",
            "message": "A user with this email already exists",
            "request_id": "test-123",
        },
    }


def test_authentication_error_adds_bearer_challenge() -> None:
    response = _client().get("/authentication")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_infrastructure_error_hides_internal_details() -> None:
    response = _client().get("/infrastructure")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["error"]["code"] == "internal_error"
    assert response.json()["error"]["message"] == "Internal server error"
    assert "private-id" not in response.text


def test_http_exception_is_normalized() -> None:
    response = _client().get("/http")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error"] == {
        "code": "http_error",
        "message": "Resource not found",
        "request_id": response.headers["X-Request-ID"],
    }


def test_validation_error_contains_only_safe_field_details() -> None:
    response = _client().post("/validation", params={"value": "not-an-int"})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["fields"][0]["path"] == ["query", "value"]
    assert "input" not in response.json()["error"]["fields"][0]


def test_unexpected_error_is_safe_for_clients() -> None:
    response = _client().get("/unexpected")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["error"]["message"] == "Internal server error"
    assert "database password" not in response.text
