# app/api/endpoints/v1/keys_and_signature/generate_dk_signature.py
from fastapi import APIRouter, status
from app.schemas.dk_signature import ReqDKSignature,DKSignatreResponse
from app.core.exceptions import CustomAPIException, HTTPExceptionError
from app.schemas.common_response import StandardResponse
from app.core.digitial_sign import  generate_signature
from loguru import logger

router = APIRouter()

@router.post(
    "",
    response_model=StandardResponse[DKSignatreResponse],
    status_code=status.HTTP_200_OK,
)
async def generate_signatures(
    *,
    req_in: ReqDKSignature,
) -> StandardResponse[DKSignatreResponse]:
    '''This API is intended for testing and developer use only.''' 
       
    try:
        private_key = None
        acc_inqry = await generate_signature(req_in)
        response_code = "0000"
        response_detail = "DK Signature fetched"
            
        return StandardResponse(
            response_code=response_code,
            response_detail=response_detail,
            response_data=acc_inqry.model_dump()
        )
        
    except CustomAPIException as e:
        logger.error(f"Error generating signature [NONCE : {req_in.nonce}] : {str(e)}")
        raise e  
    
    except Exception as e:
        logger.error(f"Error generating signature [NONCE : {req_in.nonce}] : {str(e)}")
        raise HTTPExceptionError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Exception in code",
            code="5001" 
        )
    