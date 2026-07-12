from delivery.api.v1.http.handlers.auth import router as auth_router
from delivery.api.v1.http.handlers.health import router as health_router
from delivery.api.v1.http.handlers.messages import router as messages_router
from delivery.api.v1.http.handlers.posts import router as posts_router
from delivery.api.v1.http.handlers.users import router as users_router
from delivery.api.v1.http.handlers.websocket import router as websocket_router

routers = (
    health_router,
    auth_router,
    users_router,
    posts_router,
    messages_router,
    websocket_router,
)

__all__ = ("routers",)
