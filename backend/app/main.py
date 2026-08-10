"""
RCI Code Equivalence Platform — Application Entry Point

FastAPI application factory. Registers all routers, configures middleware,
initialises the database, and wires up startup/shutdown lifecycle hooks.

SECURITY: No external API calls, no telemetry, no cloud dependencies.
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_db
from app.utils.logging import configure_logging
from app.api import health, analysis, projects

# ── Logging ────────────────────────────────────────────────────────────────────
configure_logging()
logger = logging.getLogger(__name__)

settings = get_settings()


# ── Lifespan ───────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown lifecycle."""
    logger.info("Starting RCI Code Equivalence Platform v%s", settings.app_version)
    logger.info("Running in OFFLINE mode — no external connections will be made")

    # Initialise database
    await init_db()
    logger.info("Database initialised at: %s", settings.database_url)

    yield

    logger.info("Shutting down RCI Code Equivalence Platform")


# ── App Factory ────────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Offline C ↔ Fortran Code Analysis and Equivalence Verification Platform. "
            "Operates completely without internet access."
        ),
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    # Only allow localhost origins — enforces offline-only operation
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["Content-Type", "Accept", "Authorization"],
    )

    # ── Request timing middleware ─────────────────────────────────────────────
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
        return response

    # ── Global exception handler ──────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception for %s %s: %s", request.method, request.url, exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc) if settings.debug else "An unexpected error occurred.",
                "offline": True,
            },
        )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(health.router, prefix="/api/v1", tags=["Health"])
    app.include_router(analysis.router, prefix="/api/v1", tags=["Analysis"])
    app.include_router(projects.router, prefix="/api/v1", tags=["Projects"])

    return app


app = create_app()
