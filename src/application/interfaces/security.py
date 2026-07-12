from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(kw_only=True, frozen=True, slots=True)
class IssuedAccessToken:
    value: str
    expires_at: datetime


class IPasswordHasher(Protocol):
    def hash(self, *, password: str) -> str: ...

    def verify(self, *, password: str, password_hash: str) -> bool: ...

    def verify_dummy(self, *, password: str) -> None: ...


class ITokenService(Protocol):
    def issue_access(self, *, user_id: int) -> IssuedAccessToken: ...

    def read_access_subject(self, *, token: str) -> int: ...

    def create_refresh(self) -> str: ...

    def hash_refresh(self, *, token: str) -> str: ...
