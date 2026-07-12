from pwdlib import PasswordHash


class Argon2PasswordHasher:
    def __init__(self) -> None:
        self._password_hash = PasswordHash.recommended()
        self._dummy_hash = self._password_hash.hash(
            "constant-dummy-password-never-used-for-login",
        )

    def hash(self, *, password: str) -> str:
        return self._password_hash.hash(password)

    def verify(self, *, password: str, password_hash: str) -> bool:
        return self._password_hash.verify(password, password_hash)

    def verify_dummy(self, *, password: str) -> None:
        self._password_hash.verify(password, self._dummy_hash)
