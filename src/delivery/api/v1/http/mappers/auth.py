from application.dto.auth import TokenPair
from application.dto.users import User
from delivery.api.v1.http.mappers.users import map_user_to_current_rp
from delivery.api.v1.http.schemas.auth import LoginRp, TokenPairRp


def map_token_pair_to_rp(*, tokens: TokenPair) -> TokenPairRp:
    return TokenPairRp(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        access_expires_at=tokens.access_expires_at,
        refresh_expires_at=tokens.refresh_expires_at,
    )


def map_login_to_rp(*, user: User, tokens: TokenPair) -> LoginRp:
    return LoginRp(
        **map_token_pair_to_rp(tokens=tokens).model_dump(),
        user=map_user_to_current_rp(user=user),
    )
