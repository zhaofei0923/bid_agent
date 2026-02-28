"""BidAgent V2 — FastAPI application entry point.

Configures lifespan events, exception handlers, CORS, middleware,
and mounts all v1 API routes.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.config import get_settings
from app.core.exceptions import BidAgentException
from app.core.middleware import RequestLoggingMiddleware

logger = logging.getLogger("bidagent")


# ── Lifespan ──────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown events."""
    settings = get_settings()
    logger.info(
        "Starting BidAgent %s (env=%s)", settings.APP_VERSION, settings.APP_ENV
    )

    # Validate database connection
    try:
        from sqlalchemy import text

        from app.database import engine

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection OK")
    except Exception as exc:
        logger.error("Database connection failed: %s", exc)
        raise

    # Validate Redis connection (best-effort)
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await r.ping()
        await r.aclose()
        logger.info("Redis connection OK")
    except Exception as exc:
        logger.warning("Redis not available: %s — some features disabled", exc)

    yield

    # Shutdown
    from app.database import engine

    await engine.dispose()
    logger.info("BidAgent shutdown complete")


# ── Application Factory ──────────────────────────────────────────


def create_app() -> FastAPI:
    """Build and return the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[
            "X-Credits-Consumed",
            "X-Credits-Remaining",
            "X-Process-Time",
        ],
    )

    # ── Custom middleware ─────────────────────────────────────────
    app.add_middleware(RequestLoggingMiddleware)

    # ── Exception handlers ────────────────────────────────────────
    @app.exception_handler(BidAgentException)
    async def bidagent_exception_handler(
        request: Request, exc: BidAgentException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "detail": exc.detail if exc.detail else None,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error",
                }
            },
        )

    # ── Routes ────────────────────────────────────────────────────
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    return app


# ── Module-level app instance (uvicorn entry point) ───────────────

app = create_app()
