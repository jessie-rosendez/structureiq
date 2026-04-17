import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes import health, upload, query, report
from app.core.config import get_settings
from app.core.cost_tracker import session_total_tokens, session_total_cost, reset_session

settings = get_settings()

# Set GCP credentials path before any GCP clients initialize
if settings.google_application_credentials:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials

_MAX_BODY_BYTES = 100 * 1024 * 1024  # 100 MB


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > _MAX_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={"detail": "File too large. Maximum upload size is 100 MB."},
            )
        return await call_next(request)


app = FastAPI(
    title="StructureIQ API",
    description="Grounded AEC compliance intelligence — two-layer RAG on Vertex AI",
    version="1.0.0",
)

# Body size limit must be added before CORS so it runs first
app.add_middleware(BodySizeLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(upload.router, tags=["upload"])
app.include_router(query.router, tags=["query"])
app.include_router(report.router, tags=["report"])


@app.get("/metrics", tags=["metrics"])
async def get_metrics() -> dict:
    return {
        "session_total_cost_usd": session_total_cost(),
        "total_tokens": session_total_tokens(),
    }


@app.delete("/session", tags=["session"])
async def clear_session() -> dict:
    reset_session()
    return {"message": "Session cleared. Cost tracker reset."}
