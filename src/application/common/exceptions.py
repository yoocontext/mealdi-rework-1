from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(kw_only=True, slots=True)
class AppError(Exception, ABC):
    """Root of every expected project error.

    Concrete errors own their public message. Context is represented by typed
    dataclass fields instead of positional strings assembled at raise sites.
    """

    def __post_init__(self) -> None:
        message = self.message
        if not isinstance(message, str) or not message:
            raise TypeError("Concrete AppError.message must return non-empty str")

        code = self.code
        if not isinstance(code, str) or not code:
            raise TypeError("Concrete AppError.code must return non-empty str")

        Exception.__init__(self, message)

    @property
    @abstractmethod
    def message(self) -> str:
        """Return a safe, human-readable description of the failure."""

    @property
    @abstractmethod
    def code(self) -> str:
        """Return a stable machine-readable identifier for the failure."""

    def __str__(self) -> str:
        return self.message


@dataclass(kw_only=True, slots=True)
class ApplicationError(AppError, ABC):
    """Base error for an expected application-layer failure."""


@dataclass(kw_only=True, slots=True)
class AuthenticationError(ApplicationError, ABC):
    """Base error for failed authentication."""


@dataclass(kw_only=True, slots=True)
class InvalidCredentialsError(AuthenticationError):
    @property
    def code(self) -> str:
        return "invalid_credentials"

    @property
    def message(self) -> str:
        return "Invalid email or password"


@dataclass(kw_only=True, slots=True)
class InvalidAccessTokenError(AuthenticationError):
    @property
    def code(self) -> str:
        return "invalid_access_token"

    @property
    def message(self) -> str:
        return "Invalid access token"


@dataclass(kw_only=True, slots=True)
class InvalidRefreshTokenError(AuthenticationError):
    @property
    def code(self) -> str:
        return "invalid_refresh_token"

    @property
    def message(self) -> str:
        return "Invalid refresh token"


@dataclass(kw_only=True, slots=True)
class ConflictError(ApplicationError, ABC):
    """Base error for a business uniqueness conflict."""


@dataclass(kw_only=True, slots=True)
class EmailAlreadyExistsError(ConflictError):
    @property
    def code(self) -> str:
        return "email_already_exists"

    @property
    def message(self) -> str:
        return "A user with this email already exists"


@dataclass(kw_only=True, slots=True)
class ForbiddenError(ApplicationError, ABC):
    """Base error for an operation forbidden by business rules."""


@dataclass(kw_only=True, slots=True)
class SelfMessagingError(ForbiddenError):
    @property
    def code(self) -> str:
        return "self_messaging_forbidden"

    @property
    def message(self) -> str:
        return "You cannot send a message to yourself"


@dataclass(kw_only=True, slots=True)
class PostOwnershipError(ForbiddenError):
    action: str

    @property
    def code(self) -> str:
        return "post_ownership_forbidden"

    @property
    def message(self) -> str:
        return f"Only the author can {self.action} this post"


@dataclass(kw_only=True, slots=True)
class NotFoundError(ApplicationError, ABC):
    """Base error for a missing business resource."""


@dataclass(kw_only=True, slots=True)
class UserNotFoundError(NotFoundError):
    role: str = "User"

    @property
    def code(self) -> str:
        return "user_not_found"

    @property
    def message(self) -> str:
        return f"{self.role} not found"


@dataclass(kw_only=True, slots=True)
class PostNotFoundError(NotFoundError):
    @property
    def code(self) -> str:
        return "post_not_found"

    @property
    def message(self) -> str:
        return "Post not found"
