import pytest

from application.common.exceptions import (
    AppError,
    EmailAlreadyExistsError,
    PostOwnershipError,
)
from infra.common.exceptions import InfraError
from infra.dm.exceptions import DmError, SerializationError


def test_concrete_errors_own_their_public_message() -> None:
    conflict = EmailAlreadyExistsError()
    forbidden = PostOwnershipError(action="edit")

    assert str(conflict) == conflict.message
    assert forbidden.message == "Only the author can edit this post"


def test_infrastructure_component_error_keeps_full_hierarchy() -> None:
    error = SerializationError(
        entity="post",
        identifier=42,
        operation="reload",
    )

    assert isinstance(error, DmError)
    assert isinstance(error, InfraError)
    assert isinstance(error, AppError)
    assert "post" in error.message
    assert "42" in error.message


def test_base_error_cannot_exist_without_message_contract() -> None:
    with pytest.raises(TypeError):
        AppError()  # type: ignore[abstract]
