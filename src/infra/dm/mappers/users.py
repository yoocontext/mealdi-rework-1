from application.dto.users import User
from infra.common.datetime import as_utc
from infra.orm.users import UserOrm


def map_user(*, orm: UserOrm) -> User:
    return User(
        id=orm.id,
        email=orm.email,
        name=orm.name,
        password_hash=orm.password_hash,
        created_at=as_utc(value=orm.created_at),
    )
