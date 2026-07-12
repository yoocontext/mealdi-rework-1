from dishka import Provider, Scope, provide

from bootstrap.settings import Settings
from delivery.common.settings import CookieSettings, WebSocketSettings


class SettingsProvider(Provider):
    def __init__(self, *, settings: Settings) -> None:
        super().__init__()
        self._settings = settings

    @provide(scope=Scope.APP)
    def settings(self) -> Settings:
        return self._settings

    @provide(scope=Scope.APP)
    def cookie_settings(self, *, settings: Settings) -> CookieSettings:
        return CookieSettings(
            secure=settings.cookie_secure,
            domain=settings.cookie_domain,
        )

    @provide(scope=Scope.APP)
    def websocket_settings(self, *, settings: Settings) -> WebSocketSettings:
        return WebSocketSettings(allowed_origins=frozenset(settings.cors_origins))
