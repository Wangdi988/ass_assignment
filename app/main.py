import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.router import api_router
from app.config import settings
from app.cache.redis import create_redis_pool, close_redis_pool
from app.logging_config import setup_logging, LoggerMiddleware
from app.core.exceptions import setup_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to setup and cleanup resources.
    """
    # Setup logging
    setup_logging()

    # Log application startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")


    logger.info("Setting up Redis connection pool")
    await create_redis_pool()

    logger.info("Application startup complete")

    yield

    # Cleanup connections
    logger.info("Shutting down application")

    logger.info("Closing Redis connection pool")
    await close_redis_pool()

    logger.info("Shutdown complete")


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        docs_url=f"{settings.API_PREFIX}/docs",
        redoc_url=f"{settings.API_PREFIX}/redoc",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add logging middleware
    app.add_middleware(LoggerMiddleware)

    # Setup exception handlers
    setup_exception_handlers(app)

    # Include API router
    app.include_router(api_router, prefix=settings.API_PREFIX)

    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        # log_level="info",
        # reload=settings.DEBUG,
        # workers=4,
        # limit_concurrency=10000,  # Support 10k concurrent connections
    )