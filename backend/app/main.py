from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import check_database_connection
from app.core.logging import get_logger, setup_logging
from app.modules.auth.routes import router as auth_router
from app.modules.conversations.routes import router as conversations_router
from app.modules.dashboard.routes import router as dashboard_router
from app.modules.documents.routes import router as documents_router
from app.modules.users.routes import router as users_router
from app.shared.exceptions import (
    AppException,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)

# Setup logging before anything else
setup_logging(debug=settings.DEBUG)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application startup and shutdown events."""
    logger.info(
        "app_startup",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )

    if not check_database_connection():
        logger.error("startup_database_check_failed")
        raise RuntimeError("Cannot connect to the database.")

    logger.info("startup_complete")
    yield
    logger.info("app_shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "KnowledgeHub AI — Intelligent document Q&A platform powered by RAG and Google Gemini."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Exception Handlers ───────────────────────────────────────────────────────

@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(ForbiddenError)
async def forbidden_handler(request: Request, exc: ForbiddenError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": exc.message, "code": exc.code},
    )


# ─── Routers ─────────────────────────────────────────────────────────────────

PREFIX = settings.API_V1_PREFIX

app.include_router(auth_router, prefix=PREFIX)
app.include_router(users_router, prefix=PREFIX)
app.include_router(documents_router, prefix=PREFIX)
app.include_router(conversations_router, prefix=PREFIX)
app.include_router(dashboard_router, prefix=PREFIX)


# ─── Health Check ─────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"], summary="Service health check")
def health_check() -> dict:
    db_ok = check_database_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "ok" if db_ok else "unreachable",
    }
