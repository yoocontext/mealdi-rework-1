from pathlib import Path

from fastapi.staticfiles import StaticFiles

from delivery.web.router import router

static = StaticFiles(directory=Path(__file__).parent / "static")

__all__ = ("router", "static")
