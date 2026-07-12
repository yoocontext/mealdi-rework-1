from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(include_in_schema=False)
web_root = Path(__file__).parent


@router.get("/")
async def index() -> FileResponse:
    return FileResponse(web_root / "static" / "index.html")
