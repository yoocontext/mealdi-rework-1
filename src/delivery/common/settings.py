from dataclasses import dataclass


@dataclass(kw_only=True, frozen=True, slots=True)
class CookieSettings:
    secure: bool
    domain: str | None = None


@dataclass(kw_only=True, frozen=True, slots=True)
class WebSocketSettings:
    allowed_origins: frozenset[str]

    def allows(self, *, origin: str | None) -> bool:
        return origin is None or origin in self.allowed_origins
