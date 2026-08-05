from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.core import database
from app.core.database import Base
import app.models  # Register all database models
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging, logger
from app.core.response import success_response
from app.middleware.request_context_middleware import RequestContextMiddleware
from app.middleware.security_headers_middleware import SecurityHeadersMiddleware
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.routers import auth, onboarding, users, health

# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode.")
    try:
        async with database.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Database connection error ({e}). Falling back to local SQLite database.")
        if not settings.DATABASE_URL.startswith("sqlite"):
            database.engine = database._create_engine_for_url("sqlite+aiosqlite:///./ofc_hr.db")
            database.AsyncSessionLocal.configure(bind=database.engine)
            async with database.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Local SQLite fallback database initialized successfully.")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise-Grade Authentication & Onboarding Backend for OFC HR",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Middlewares
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestContextMiddleware)

# Register Exception Handlers
register_exception_handlers(app)


@app.get("/", tags=["Root"])
async def root(request: Request):
    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data={
            "app_name": settings.APP_NAME,
            "version": "1.0.0",
            "documentation": "/docs",
            "redoc": "/redoc",
            "health": "/health"
        },
        message="Welcome to OFC HR Enterprise Backend API",
        request_id=request_id
    )


# Include Routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(onboarding.router)
app.include_router(users.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
