# app/core/digitial_sign/digitial_sign.py
# jwt from pyjwt
import jwt
import datetime
from fastapi import status
from app.config import settings
from app.core.exceptions import AuthenticationError, HTTPExceptionError
import json
from app.schemas.dk_signature import ReqDKSignature, DKSignatreResponse
from fastapi import Request 
from loguru import logger
from app.cache.redis import RedisCache
from app.schemas.token import NonceUsed
import base64
from pathlib import Path
import time


nonce_cache = RedisCache(prefix="nonce", model_class=NonceUsed)

async def generate_signature(req: ReqDKSignature) -> DKSignatreResponse:
    
    
    private_key_path = Path(settings.SECRETS_DIR) / "private_key.pem"
    PRIVATE_KEY_PEM = private_key_path.read_text()
    

    # Log the raw request body
    logger.info(f"Raw request body: {req.request_body}")

    # Convert request_body to sorted JSON string (canonical)
    request_body_str = json.dumps(req.request_body, sort_keys=True, separators=(",", ":"))
    logger.info(f"Canonical JSON body: {request_body_str}")

    # Base64 encode the request body
    body_base64 = base64.b64encode(request_body_str.encode()).decode()
    logger.info(f"Base64-encoded body: {body_base64}")

    current_time = datetime.datetime.now(datetime.timezone.utc)
    # Expiration timestamp in epoch seconds
    expiration_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=50)
    expiration_ts = int(expiration_dt.timestamp())  # Correct UTC timestamp
    
    logger.info(f"CurrentTime: {current_time}")
    logger.info(f"expiration_dt:{expiration_dt}")
    logger.info(f"expiration_ts:{expiration_ts}")
    
    # Log nonce and timestamp
    logger.info(f"Nonce: {req.nonce}")
    logger.info(f"Timestamp: {req.timestamp}")

    # Create JWT payload (claims)
    payload = {
        "nonce": req.nonce,
        "timestamp": req.timestamp,
        "exp": expiration_ts,
        "data": body_base64
    }
    
    logger.info(f"JWT Payload: {json.dumps(payload, indent=2)}")
    # Encode JWT
    dk_signature = jwt.encode(payload, PRIVATE_KEY_PEM, algorithm="RS256")
    logger.info(f"Generated DK Signature (JWT): {dk_signature}")

    return DKSignatreResponse(
        dk_signature=dk_signature,
        type="RS256"
    )
    



# Function to validate the signature
async def validate_signature(request_body: dict, headers: dict):
    private_key_path = Path(settings.SECRETS_DIR) / "public_key.pem"
    PUBLIC_KEY_PEM = private_key_path.read_text()

    def parse_utc(ts_str: str) -> datetime.datetime:
        return datetime.datetime.strptime(ts_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc)

    common_resp = AuthenticationError(
        status_code=status.HTTP_401_UNAUTHORIZED,
        message="Invalid signature",
        code="4006"
    )

    try:
        # Extract DK-Signature header
        signature_header = headers.get('DK-Signature')
        expected_prefix = "DKSignature "
        
        
        if not signature_header:
            logger.info("Missing DK-Signature header")
            raise common_resp

        if not signature_header.startswith(expected_prefix):
            logger.info(f"Invalid DK-Signature header format: {signature_header}")
            raise common_resp
        
        token = signature_header[len(expected_prefix):]

        # Decode claims WITHOUT verification
        unverified_claims = jwt.decode(token, options={"verify_signature": False})
        logger.info(f"Unverified JWT claims: {unverified_claims}")
        
        # Validate presence of required claims early
        # required_claims = ["nonce", "timestamp", "exp", "data"]
        required_claims = ["nonce", "timestamp", "exp", "data"]
        for claim in required_claims:
            if claim not in unverified_claims:
                logger.info(f"Missing claim in JWT payload: '{claim}' (got keys: {list(unverified_claims.keys())})")
                raise AuthenticationError(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    message=f"Missing '{claim}' claim in JWT payload",
                    code="4006"
                )


        exp = unverified_claims.get("exp")
        logger.info(f"Token exp claim (unix timestamp): {exp}")

        if not isinstance(exp, (int, float)):
            logger.info(f"Invalid exp claim format: expected numeric UNIX timestamp, got: {exp} (type: {type(exp)})")
            raise common_resp
        exp_dt = datetime.datetime.fromtimestamp(exp, tz=datetime.timezone.utc)
        logger.info(f"Token exp datetime (UTC): {exp_dt.isoformat()}")

        # Single reference timestamp
        now_ts = int(time.time())
        now_dt_utc = datetime.datetime.fromtimestamp(now_ts, tz=datetime.timezone.utc)
        now_dt_local = datetime.datetime.fromtimestamp(now_ts)

        logger.info("=== TIME COMPARISION ===")
        logger.info(f"Current UNIX timestamp: {now_ts}")
        logger.info(f"Current UTC datetime: {now_dt_utc.isoformat()}")
        logger.info(f"Current LOCAL datetime: {now_dt_local.isoformat()}")

        exp_dt = datetime.datetime.fromtimestamp(exp, tz=datetime.timezone.utc)
        logger.info(f"Token exp UTC datetime: {exp_dt.isoformat()}")

        delta = exp_dt - now_dt_utc
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(abs(total_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        logger.info(f"Delta total seconds: {total_seconds} | positive: valid | negative: expired")
        
        if total_seconds >= 0:
            logger.info(f"Token valid. Time until expiration: {hours}h {minutes}m {seconds}s")
        else:
            logger.info(f"Token expired {hours}h {minutes}m {seconds}s ago")
            raise AuthenticationError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Signature has expired",
                code="4006"
            )

        # Decode JWT (validate signature)
        decoded_signature = jwt.decode(
            token,
            PUBLIC_KEY_PEM,
            algorithms=["RS256"]
        )

        # Validate request body
        body_base64 = decoded_signature["data"]
        decoded_body = base64.b64decode(body_base64).decode()

        request_body_str = json.dumps(request_body, sort_keys=True, separators=(",", ":"))

        logger.info(f"Incoming request data: {request_body_str}")
        logger.info(f"Decoded signature body: {decoded_body}")

        if decoded_body != request_body_str:
            logger.info("Signature data mismatch")
            raise common_resp

        # Validate timestamp
        request_timestamp = headers.get("DK-Timestamp")
        if not request_timestamp:
            logger.info("Missing DK-Timestamp header")
            raise common_resp

        signature_timestamp = decoded_signature.get("timestamp")
        if not signature_timestamp:
            logger.info("Missing timestamp in signature")
            raise common_resp

        request_ts_dt = parse_utc(request_timestamp)
        signature_ts_dt = parse_utc(signature_timestamp)

        delta_seconds = abs((request_ts_dt - signature_ts_dt).total_seconds())
        if delta_seconds > 5 * 60:
            logger.info(f"Timestamp mismatch | Request: {request_ts_dt} | Signature: {signature_ts_dt}")
            raise common_resp

        # Validate nonce
        dk_nonce = headers.get("DK-Nonce")
        
        if not dk_nonce:
            logger.info("Missing DK-Nonce header")
            raise common_resp

        nonce = decoded_signature.get("nonce")
        if not nonce:
            logger.info("Missing nonce in signature")
            raise common_resp

        cache_key = str(nonce)
        cached_nonce = await nonce_cache.get(cache_key)
        if cached_nonce:
            print("Nounce is already used")
            logger.info(f"Nonce already used: {nonce}")
            raise common_resp
            # raise AuthenticationError(
            #         status_code=status.HTTP_401_UNAUTHORIZED,
            #         message="Invalid signature",
            #         code="4006"
            #     )

        if dk_nonce != nonce:
            logger.info(f"Nonce mismatch | Header: {dk_nonce} | Signature: {nonce}")
            raise common_resp

        # Mark nonce as used
        nonce_status = NonceUsed(status="used")
        await nonce_cache.set(cache_key, nonce_status, expire=86400)

        logger.info("DK Signature validated successfully")
        return True

    
    except jwt.InvalidTokenError as ive:
        logger.error(f"Invalid JWT: {ive}")
        raise common_resp
    
    except AuthenticationError as e:
        print("An unexpected error occurred Invalid signature")
        logger.info(f"Authentication error: {e}")
        raise common_resp
    
    # except AuthenticationError as e:
    #     logger.error(f"Authentication error: {e}")
    #     raise e
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPExceptionError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Exception in code",
            code="5001"
        )

async def validate_signature_dependency(request: Request):
    raw_body = await request.body()
    request_body_dict = json.loads(raw_body)

    auth_response = await validate_signature(
        headers=request.headers,
        request_body=request_body_dict
    )
    if auth_response:
        return auth_response
    # else:
    #     return auth_response

    

    





# from app.core.digitial_sign.signature_helper import extract_form_fields_for_signature, get_signature_string

from app.core.signature_helper import (
    extract_form_fields_for_signature, 
    extract_query_params_for_signature,
    get_signature_string
)

async def file_validate_signature_dependency(request: Request):
    content_type = request.headers.get("content-type", "").lower()
    method = request.method
    
    try:
        if method == "GET":
            # Use helper for GET requests
            query_params = dict(request.query_params)
            request_body_dict = extract_query_params_for_signature(query_params)
            
            logger.info(f"GET signature validation | Params: {list(request_body_dict.keys())}")
            logger.info(f"Signature body string: {get_signature_string(request_body_dict)}")
            
        elif content_type.startswith("application/json"):
            raw_body = await request.body()
            request_body_dict = json.loads(raw_body.decode("utf-8") or "{}")
            
            logger.info(f"JSON signature validation")
            logger.info(f"Signature body string: {get_signature_string(request_body_dict)}")
           
        elif content_type.startswith("multipart/form-data"):
            form = await request.form()
            logger.info(f"Form-data received with {len(form)} fields")
           
            # Use helper to extract and sort fields
            request_body_dict = extract_form_fields_for_signature(dict(form))
           
            logger.info(f"Fields for signature validation: {list(request_body_dict.keys())}")
            logger.info(f"Signature body string: {get_signature_string(request_body_dict)}")
           
        else:
            logger.warning(f"Unsupported content type: {content_type}")
            request_body_dict = {}
           
    except UnicodeDecodeError as ude:
        logger.error(f"Unicode decode error: {ude}")
        raise HTTPExceptionError(status_code=400, detail="Invalid request encoding")
       
    except Exception as e:
        logger.error(f"Failed to parse request body: {e}")
        raise HTTPExceptionError(status_code=400, detail="Invalid request body")
   
    # Validate signature
    auth_response = await validate_signature(
        request_body=request_body_dict,
        headers=request.headers
    )
   
    if auth_response:
        return auth_response