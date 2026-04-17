from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": "structureiq-backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
