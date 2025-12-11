from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from redis.asyncio import Redis
from loguru import logger
from app.config import settings
from app.cache.redis import get_redis
from app.core.exceptions import AuthenticationError

# OAuth2 password bearer scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_PREFIX}/auth/token"
)


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        redis: Redis = Depends(get_redis),
):
    """
    Dependency to get the current authenticated user.

    Validates JWT token and returns user information.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "response_code": "authentication_error",
            "response_detail": "Could not validate credentials",
            "response_data": None
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Implement JWT validation
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        # Check token expiration
        exp = payload.get("exp")
        if exp is None or datetime.utcnow().timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "response_code": "token_expired",
                    "response_detail": "Token has expired",
                    "response_data": None
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user exists in authorized users
        auth_users = settings.get_auth_users()
        if auth_users and username not in auth_users:
            logger.error(f"User {username} not found in authorized users")
            raise credentials_exception

        # Create a simple user object
        user = {
            "username": username,
            "is_active": True
        }

        return user
    except ExpiredSignatureError:
        raise AuthenticationError(
        status_code=status.HTTP_401_UNAUTHORIZED,
        message="Token has expired",
        code="4007"
    )
    
    except JWTError:
        print("JWT validation error:>>>")
        logger.error("JWT validation error")
        raise credentials_exception
    except Exception as e:
        print("Authentication error:>>>")
        logger.error(f"Authentication error: {str(e)}")
        raise credentials_exception
