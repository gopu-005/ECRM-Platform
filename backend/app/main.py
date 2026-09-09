"""
ECRM Platform — FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import logging

from app.core.config import settings
from app.core.database import create_tables
from app.core.redis import get_redis, close_redis

# Routers
from app.api.v1.auth import router as auth_router
from app.api.v1.leads import router as leads_router
from app.api.v1.contacts import router as contacts_router
from app.api.v1.accounts import router as accounts_router
from app.api.v1.deals import router as deals_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.meetings import router as meetings_router
from app.api.v1.activities import activities_router, notifications_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.admin import router as admin_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    logger.info("Starting ECRM Platform API...")
    # Initialize Redis connection
    await get_redis()
    # Create tables in development
    if settings.is_development:
        await create_tables()
        logger.info("Database tables created/verified.")
    yield
    # Cleanup
    await close_redis()
    logger.info("ECRM Platform API shut down.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## ECRM Platform API

A production-grade multi-tenant CRM platform built with FastAPI.

### Features
- 🔐 Multi-tenant isolation (row-level security)
- 👥 Role-based access control (RBAC)
- 📊 Advanced analytics (20+ KPIs)
- 🔄 Background task processing (Celery)
- 📥 CSV import/export
- 🏗️ Sales pipeline management
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ── Routes ────────────────────────────────────────────────────────────────────
API_PREFIX = settings.API_V1_PREFIX

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(leads_router, prefix=API_PREFIX)
app.include_router(contacts_router, prefix=API_PREFIX)
app.include_router(accounts_router, prefix=API_PREFIX)
app.include_router(deals_router, prefix=API_PREFIX)
app.include_router(tasks_router, prefix=API_PREFIX)
app.include_router(meetings_router, prefix=API_PREFIX)
app.include_router(activities_router, prefix=API_PREFIX)
app.include_router(notifications_router, prefix=API_PREFIX)
app.include_router(analytics_router, prefix=API_PREFIX)
app.include_router(admin_router, prefix=API_PREFIX)


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    return JSONResponse({
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    })


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to ECRM Platform API",
        "docs": "/docs",
        "health": "/health",
        "version": settings.APP_VERSION,
    }
