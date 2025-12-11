from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger
# from sqlalchemy.exc import SQLAlchemyError
from redis.exceptions import RedisError
from pydantic import ValidationError


class APIException(Exception):
    """Base API exception class."""

    def __init__(
            self,
            status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
            message: str = "An unexpected error occurred",
            code: str = "internal_error"
    ):
        self.status_code = status_code
        self.message = message
        self.code = code
        super().__init__(self.message)



class CustomException(APIException):
    """ General errors."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "5001",
        message: str = "An unexpected error occurred."
    ):
        super().__init__(
            status_code=status_code,
            message=message,
            code=code
        )

class ValidationRequestError(APIException):
    """Validation error."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            code="validation_error"
        )


class RedisCacheError(APIException):
    """Redis cache error."""

    def __init__(self, message: str = "Cache error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            code="cache_error"
        )

class HTTPExceptionError(HTTPException):
    """Base API exception class."""

    def __init__(
            self,
            status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
            message: str = "An unexpected HTTP error occurred",
            code: str = "http_internal_error"
    ):
        self.status_code = status_code
        self.message = message
        self.code = code
        super().__init__(self.message)


class AuthenticationError(APIException):
    """ General errors."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "5001",
        message: str = "An unexpected error occurred."
    ):
        super().__init__(
            status_code=status_code,
            message=message,
            code=code
        )

class CustomAPIException(APIException):
    """ General errors."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "5001",
        message: str = "An unexpected error occurred."
    ):
        super().__init__(
            status_code=status_code,
            message=message,
            code=code
        )


# async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
#     """Handler for validation exceptions."""
#     errors = []
#     for error in exc.errors():
#         location = ".".join([str(loc) for loc in error["loc"]])
#         errors.append({
#             "location": location,
#             "message": error["msg"],
#             "type": error["type"],
#         })

#     logger.error(f"Validation Error: {errors}")
#     return JSONResponse(
#         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#         content={
#             "response_code": "validation_error",
#             "response_detail": "Validation error",
#             "response_data": {"errors": errors}
#         }
#     )


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Handler for API exceptions."""
    logger.error(f"API Exception: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "response_code": exc.code,
            "response_detail": exc.message,
            "response_data": None
        }
    )

async def http_exception_handler(request: Request, exc: HTTPExceptionError) -> JSONResponse:
    """Handler for API exceptions."""
    logger.error(f"HTTP Exception: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "response_code": exc.status_code,
            "response_detail": exc.detail,
            "response_data": None
        }
    )


async def redis_exception_handler(request: Request, exc: RedisError) -> JSONResponse:
    """Handler for Redis exceptions."""
    logger.error(f"Redis Error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "response_code": "cache_error",
            "response_detail": f"A cache error occurred {str(exc)}",
            "response_data": None
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for unhandled exceptions."""
    logger.error(f"Unhandled Exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "response_code": "internal_error",
            "response_detail": f"An unexpected error occurred {str(exc)}",
            "response_data": None
        }
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers with the FastAPI app."""
    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(RedisError, redis_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)