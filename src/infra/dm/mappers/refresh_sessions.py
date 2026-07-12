from application.dto.auth import RefreshSession
from infra.common.datetime import as_utc
from infra.orm.refresh_sessions import RefreshSessionOrm


def map_refresh_session(*, orm: RefreshSessionOrm) -> RefreshSession:
    return RefreshSession(
        id=orm.id,
        user_id=orm.user_id,
        token_hash=orm.token_hash,
        expires_at=as_utc(value=orm.expires_at),
        revoked_at=(
            as_utc(value=orm.revoked_at) if orm.revoked_at is not None else None
        ),
        created_at=as_utc(value=orm.created_at),
    )
