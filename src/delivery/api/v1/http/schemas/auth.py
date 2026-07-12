from datetime import datetime

from pydantic import BaseModel, Field

from delivery.api.v1.http.schemas.users import CurrentUserRp


class RefreshTokenRq(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=256)


class TokenPairRp(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    access_expires_at: datetime
    refresh_expires_at: datetime


class LoginRp(TokenPairRp):
    user: CurrentUserRp


class LogoutRp(BaseModel):
    ok: bool = True
