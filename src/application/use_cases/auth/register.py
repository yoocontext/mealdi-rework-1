from dataclasses import dataclass

from application.common.exceptions import EmailAlreadyExistsError
from application.common.use_case import BaseUseCase
from application.dto.users import User
from application.interfaces.dm.users import IUserDm
from application.interfaces.security import IPasswordHasher
from application.interfaces.transaction import ITransactionManager


@dataclass(kw_only=True, frozen=True, slots=True)
class RegisterUserCm:
    email: str
    name: str
    password: str


@dataclass(kw_only=True, frozen=True, slots=True)
class RegisterUserRs:
    user: User


@dataclass(kw_only=True, slots=True)
class RegisterUserUc(BaseUseCase[RegisterUserCm, RegisterUserRs]):
    """Create a unique user account.

    Pipeline:
    1. Normalize identity fields and check email uniqueness.
    2. Hash the password and persist the user.
    3. Commit and return the created account.

    Edge cases:
    - An existing normalized email produces a conflict.
    """

    _users: IUserDm
    _passwords: IPasswordHasher
    _transaction: ITransactionManager

    async def act(self, *, command: RegisterUserCm) -> RegisterUserRs:
        email = self._normalize_email(email=command.email)

        await self._require_available_email(email=email)

        user = await self._create_user(
            email=email,
            name=command.name,
            password=command.password,
        )
        await self._transaction.commit()

        return RegisterUserRs(user=user)

    def _normalize_email(self, *, email: str) -> str:
        return email.strip().casefold()

    async def _require_available_email(self, *, email: str) -> None:
        if await self._users.get_by_email(email=email) is not None:
            raise EmailAlreadyExistsError()

    async def _create_user(self, *, email: str, name: str, password: str) -> User:
        password_hash = self._passwords.hash(password=password)

        return await self._users.create(
            email=email,
            name=name.strip(),
            password_hash=password_hash,
        )
