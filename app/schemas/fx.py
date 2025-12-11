from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class FxBase(BaseModel):
    """Base schema for FX."""
    pass

    # name: str = Field(..., min_length=1, max_length=255, example="YJ Product")
    # description: Optional[str] = Field(None, example="This is a YJ product.")
    # price: int = Field(..., gt=0, example=2025)  # Price in cents
    # is_active: bool = Field(True, example=True)


class GetFx(FxBase):
    """Schema for retrieving fx rate."""
    date_time: datetime = Field(..., example="2025-11-23 12:12:30.897")
    alpha_currency_code: str = Field(..., example="USD")


class FxResponse(BaseModel):
    """Schema for Item response."""
    date_time: datetime = Field(..., example="2025-11-23 12:12:30.897")
    currency_code: str = Field(..., example="USD")
    buy_rate: float =  Field(..., example="130.31")
    sell_rate: float = Field(..., example="134.67")