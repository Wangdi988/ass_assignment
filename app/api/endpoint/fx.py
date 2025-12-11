from datetime import datetime
from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis
from loguru import logger

from app.cache.redis import get_redis

from app.core.dependencies import get_current_user
from app.core.digitial_sign import validate_signature_dependency
from app.core.exceptions import CustomAPIException, CustomException
from app.schemas.fx import GetFx
from app.service.fx_service import fx_rate_service

router = APIRouter()

from app.schemas.common_response import StandardResponse

@router.post(
    "/read",
    response_model=StandardResponse,
    summary="Retrieve Fx rate",
    description="Retrive Fx rate details",
    response_description="The get fx rate",
)
async def read_fx(
        *,
        data_in: GetFx,
        redis: Redis = Depends(get_redis),
        current_user: dict = Depends(get_current_user),
        _ = Depends(validate_signature_dependency),
) -> StandardResponse:
    """
    To get requested fx rate.
    """
    try:
        
        logger.info(f"fx requested data: {data_in}")
        ts_now = datetime.now()
        fx_rate =  await fx_rate_service(data_in.alpha_currency_code, data_in.date_time)
        logger.info(f"fx rate response data: {fx_rate}")

        logger.info(f"Response time taken: {datetime.now() - ts_now}")
        return StandardResponse(
            response_code="0000",
            response_detail="Fx rate successfully retrieve",
            response_data=fx_rate.model_dump()
        )
    except CustomException as e:
        logger.info(f"Custom exception message: {e.message}. |  {str(e)}")
        return StandardResponse(
            response_code= e.code,
            response_detail= e.message,
            response_data=None,
        )
    
    except Exception as e:
        logger.info(f"Error getting fx rate {data_in}: {str(e)}")
        return StandardResponse(
            response_code= '5001',
            response_detail= 'An unexpected error occurred',
            response_data=None,
        )