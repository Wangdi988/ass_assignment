import sys
from datetime import datetime
from pathlib import Path
import logging
from logging.handlers import TimedRotatingFileHandler

from loguru import logger

from app.config import settings


def setup_logging():
    """Configure logging with separate files for errors and access logs."""
    # Create log directory if it doesn't exist
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Log file naming pattern
    today = datetime.now().strftime("%d%m%Y")
    error_log_path = log_dir / f"{today}_error.log"
    access_log_path = log_dir / f"{today}_access.log"

    # Configure loguru
    config = {
        "handlers": [
            {
                "sink": sys.stdout,
                "level": settings.LOG_LEVEL,
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            },
            {
                "sink": error_log_path,
                "level": "ERROR",
                "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
                "rotation": "00:00",  # Rotate at midnight
                "retention": "30 days",  # Keep logs for 30 days
                "compression": "gz",  # Compress rotated logs
            },
            {
                "sink": access_log_path,
                "level": "INFO",
                "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
                "filter": lambda record: record["level"].name != "ERROR",
                "rotation": "00:00",  # Rotate at midnight
                "retention": "30 days",  # Keep logs for 30 days
                "compression": "gz",  # Compress rotated logs
            },
        ],
    }

    # Remove existing loggers and apply new config
    logger.remove()
    for handler in config["handlers"]:
        logger.configure(handlers=[handler])

    # Intercept standard library logging
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # Find caller from where originated the logged message
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Replace libraries loggers
    for lib_logger in [
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
        "sqlalchemy",
        "aio_pika",
        "asyncpg",
        "redis",
    ]:
        logging.getLogger(lib_logger).handlers = [InterceptHandler()]
        logging.getLogger(lib_logger).propagate = False

    logger.info(f"Logging initialized with level {settings.LOG_LEVEL}")


class LoggerMiddleware:
    """Middleware for logging HTTP requests."""

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = datetime.now()

        # Create a response interceptor
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]
                duration = (datetime.now() - start_time).total_seconds() * 1000
                path = scope.get("path", "")
                method = scope.get("method", "")

                # Log request based on status code
                log_msg = f"{method} {path} - {status_code} - {duration:.2f}ms"

                if 400 <= status_code < 600:
                    logger.error(log_msg)
                else:
                    logger.info(log_msg)

            await send(message)

        await self.app(scope, receive, send_wrapper)

    def __init__(self, app):
        self.app = app