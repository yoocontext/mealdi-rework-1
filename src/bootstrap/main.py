from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bootstrap.ioc.container import create_container
from bootstrap.settings import Settings
from delivery.api.v1.http.exceptions import install_application_error_handlers
from delivery.api.v1.http.handlers import routers
from delivery.api.v1.http.request_id import install_request_id_middleware
from delivery.web import router as web_router
from delivery.web import static as web_static


def create_app(*, settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings()
    container = create_container(settings=resolved_settings)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        yield
        await container.close()

    app = FastAPI(title="Mealdi API", version="1.0.0", lifespan=lifespan)
    install_request_id_middleware(app=app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    for router in routers:
        app.include_router(router)
    app.include_router(web_router)
    app.mount("/static", web_static, name="static")

    install_application_error_handlers(app=app)
    setup_dishka(container, app)

    return app


app = create_app()
