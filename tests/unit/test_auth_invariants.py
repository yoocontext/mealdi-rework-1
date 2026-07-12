from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from application.common.exceptions import (
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from application.dto.auth import RefreshSession
from application.dto.users import User
from application.interfaces.security import IssuedAccessToken
from application.use_cases.auth.login import LoginCm, LoginUc
from application.use_cases.auth.refresh import RefreshTokensCm, RefreshTokensUc

NOW = datetime(2026, 7, 12, 10, tzinfo=UTC)
USER = User(
    id=7,
    email="alice@example.com",
    name="Alice",
    password_hash="stored-password-hash",
    created_at=NOW,
)


def _login_use_case(
    *,
    users: AsyncMock,
    sessions: AsyncMock,
    passwords: Mock,
    tokens: Mock,
    transaction: AsyncMock,
) -> LoginUc:
    clock = Mock()
    clock.now.return_value = NOW

    return LoginUc(
        _users=users,
        _sessions=sessions,
        _passwords=passwords,
        _tokens=tokens,
        _clock=clock,
        _transaction=transaction,
        _refresh_ttl=timedelta(days=14),
    )


@pytest.mark.parametrize(
    "found_user", [None, USER], ids=["unknown-email", "bad-password"]
)
async def test_invalid_login_never_opens_or_commits_a_session(
    *,
    found_user: User | None,
) -> None:
    users = AsyncMock()
    users.get_by_email.return_value = found_user
    sessions = AsyncMock()
    passwords = Mock()
    passwords.verify.return_value = False
    tokens = Mock()
    transaction = AsyncMock()
    use_case = _login_use_case(
        users=users,
        sessions=sessions,
        passwords=passwords,
        tokens=tokens,
        transaction=transaction,
    )

    with pytest.raises(InvalidCredentialsError):
        await use_case.act(
            command=LoginCm(email=" Alice@Example.com ", password="wrong"),
        )

    users.get_by_email.assert_awaited_once_with(email="alice@example.com")
    if found_user is None:
        passwords.verify_dummy.assert_called_once_with(password="wrong")
    else:
        passwords.verify.assert_called_once_with(
            password="wrong",
            password_hash=USER.password_hash,
        )
    sessions.create.assert_not_awaited()
    transaction.commit.assert_not_awaited()


async def test_login_persists_only_refresh_digest_before_commit() -> None:
    users = AsyncMock()
    users.get_by_email.return_value = USER
    sessions = AsyncMock()
    passwords = Mock()
    passwords.verify.return_value = True
    tokens = Mock()
    tokens.issue_access.return_value = IssuedAccessToken(
        value="access-token",
        expires_at=NOW + timedelta(minutes=15),
    )
    tokens.create_refresh.return_value = "secret-refresh-token"
    tokens.hash_refresh.return_value = "refresh-digest"
    transaction = AsyncMock()
    use_case = _login_use_case(
        users=users,
        sessions=sessions,
        passwords=passwords,
        tokens=tokens,
        transaction=transaction,
    )

    result = await use_case.act(
        command=LoginCm(email=USER.email, password="correct"),
    )

    sessions.create.assert_awaited_once_with(
        user_id=USER.id,
        token_hash="refresh-digest",
        expires_at=NOW + timedelta(days=14),
    )
    transaction.commit.assert_awaited_once_with()
    assert result.tokens.refresh_token == "secret-refresh-token"


def _session(
    *,
    expires_at: datetime = NOW + timedelta(days=1),
    revoked_at: datetime | None = None,
) -> RefreshSession:
    return RefreshSession(
        id=11,
        user_id=USER.id,
        token_hash="hash:old-refresh",
        expires_at=expires_at,
        revoked_at=revoked_at,
        created_at=NOW - timedelta(days=1),
    )


def _refresh_use_case(
    *,
    found_session: RefreshSession | None,
    found_user: User | None = USER,
) -> tuple[RefreshTokensUc, AsyncMock, AsyncMock, AsyncMock]:
    sessions = AsyncMock()
    sessions.get_by_hash.return_value = found_session
    users = AsyncMock()
    users.get_by_id.return_value = found_user
    tokens = Mock()
    tokens.hash_refresh.side_effect = lambda *, token: f"hash:{token}"
    tokens.create_refresh.return_value = "new-refresh"
    tokens.issue_access.return_value = IssuedAccessToken(
        value="new-access",
        expires_at=NOW + timedelta(minutes=15),
    )
    clock = Mock()
    clock.now.return_value = NOW
    transaction = AsyncMock()

    use_case = RefreshTokensUc(
        _sessions=sessions,
        _users=users,
        _tokens=tokens,
        _clock=clock,
        _transaction=transaction,
        _refresh_ttl=timedelta(days=14),
    )
    return use_case, sessions, users, transaction


@pytest.mark.parametrize(
    "found_session",
    [
        None,
        _session(revoked_at=NOW - timedelta(minutes=1)),
        _session(expires_at=NOW),
    ],
    ids=["missing", "revoked", "expired"],
)
async def test_inactive_refresh_token_cannot_mutate_state(
    *,
    found_session: RefreshSession | None,
) -> None:
    use_case, sessions, users, transaction = _refresh_use_case(
        found_session=found_session,
    )

    with pytest.raises(InvalidRefreshTokenError):
        await use_case.act(command=RefreshTokensCm(refresh_token="old-refresh"))

    sessions.get_by_hash.assert_awaited_once_with(
        token_hash="hash:old-refresh",
        for_update=True,
    )
    users.get_by_id.assert_not_awaited()
    sessions.save.assert_not_awaited()
    sessions.create.assert_not_awaited()
    transaction.commit.assert_not_awaited()


async def test_orphaned_refresh_session_cannot_be_rotated() -> None:
    use_case, sessions, _, transaction = _refresh_use_case(
        found_session=_session(),
        found_user=None,
    )

    with pytest.raises(InvalidRefreshTokenError):
        await use_case.act(command=RefreshTokensCm(refresh_token="old-refresh"))

    sessions.save.assert_not_awaited()
    sessions.create.assert_not_awaited()
    transaction.commit.assert_not_awaited()


async def test_refresh_rotation_revokes_old_session_and_commits_replacement() -> None:
    old_session = _session()
    use_case, sessions, _, transaction = _refresh_use_case(
        found_session=old_session,
    )

    result = await use_case.act(
        command=RefreshTokensCm(refresh_token="old-refresh"),
    )

    revoked = sessions.save.await_args.kwargs["session"]
    assert revoked.id == old_session.id
    assert revoked.revoked_at == NOW
    sessions.create.assert_awaited_once_with(
        user_id=USER.id,
        token_hash="hash:new-refresh",
        expires_at=NOW + timedelta(days=14),
    )
    transaction.commit.assert_awaited_once_with()
    assert result.tokens.refresh_token == "new-refresh"
