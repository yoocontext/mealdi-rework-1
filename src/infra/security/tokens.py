import hashlib
import hmac
import secrets
from datetime import timedelta

import jwt

from application.common.exceptions import InvalidAccessTokenError
from application.interfaces.clock import IClock
from application.interfaces.security import IssuedAccessToken, ITokenService


class JwtTokenService(ITokenService):
    def __init__(
        self,
        *,
        secret: str,
        issuer: str,
        audience: str,
        access_ttl: timedelta,
        clock: IClock,
    ) -> None:
        self._secret = secret
        self._issuer = issuer
        self._audience = audience
        self._access_ttl = access_ttl
        self._clock = clock

    def issue_access(self, *, user_id: int) -> IssuedAccessToken:
        issued_at = self._clock.now()
        expires_at = issued_at + self._access_ttl
        value = jwt.encode(
            {
                "sub": str(user_id),
                "iat": issued_at,
                "exp": expires_at,
                "typ": "access",
                "iss": self._issuer,
                "aud": self._audience,
                "jti": secrets.token_urlsafe(16),
            },
            self._secret,
            algorithm="HS256",
        )
        return IssuedAccessToken(value=value, expires_at=expires_at)

    def read_access_subject(self, *, token: str) -> int:
        payload = self._decode(token=token)
        self._require_access_type(payload=payload)

        return self._read_subject(payload=payload)

    def _decode(self, *, token: str) -> dict[str, object]:
        try:
            return jwt.decode(
                token,
                self._secret,
                algorithms=["HS256"],
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["sub", "iat", "exp", "typ", "jti"]},
            )
        except jwt.PyJWTError as exc:
            raise InvalidAccessTokenError() from exc

    def _require_access_type(self, *, payload: dict[str, object]) -> None:
        if payload.get("typ") != "access":
            raise InvalidAccessTokenError()

    def _read_subject(self, *, payload: dict[str, object]) -> int:
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject.isdecimal():
            raise InvalidAccessTokenError()

        user_id = int(subject)
        if user_id == 0:
            raise InvalidAccessTokenError()

        return user_id

    def create_refresh(self) -> str:
        return secrets.token_urlsafe(48)

    def hash_refresh(self, *, token: str) -> str:
        return hmac.new(
            self._secret.encode(),
            token.encode(),
            hashlib.sha256,
        ).hexdigest()
