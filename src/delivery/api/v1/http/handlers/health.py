from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/http", tags=["system"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
