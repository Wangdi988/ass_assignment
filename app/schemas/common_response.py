from typing import Generic, List, Optional, TypeVar, Dict, Any, Union
from pydantic import BaseModel, Field

# Type variable for generic response
T = TypeVar('T')


class StandardResponse(BaseModel, Generic[T]):
    """
    Standard response model for all API responses.

    Attributes:
        response_code: String code indicating the result status
        response_detail: Human-readable message about the response
        response_data: The actual response data
    """
    response_code: str = Field(..., example="success")
    response_detail: str = Field(..., example="Operation completed successfully")
    response_data: Union[List[T], Dict[str, Any], None] = Field(default=None)


# Common response types
class HealthCheckData(BaseModel):
    """Health check response data model."""
    status: str = Field(..., example="ok")
    database: str = Field(..., example="ok")
    redis: str = Field(..., example="ok")
    rabbitmq: str = Field(..., example="ok")
    overall: str = Field(..., example="ok")


class MessageResponse(BaseModel):
    """Simple message response model."""
    message: str = Field(..., example="Operation completed successfully")


# Type aliases for commonly used response types
HealthResponse = StandardResponse[HealthCheckData]
MessageResponseType = StandardResponse[MessageResponse]