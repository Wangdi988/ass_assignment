from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError

from app.config import settings
from app.schemas.common_response import StandardResponse
from app.schemas.token import Token

router = APIRouter()


@router.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    # Get authorized users from settings
    auth_users = settings.get_auth_users()

    # Check if username exists and password matches
    if form_data.username not in auth_users or auth_users[form_data.username] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token with expiration
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Current time for token creation
    now = datetime.utcnow()

    # JWT payload
    payload = {
        "sub": form_data.username,  # Subject (the user)
        "iat": now,  # Issued at
        "exp": now + access_token_expires,  # Expiration time
    }

    # Create JWT token
    access_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/verify", response_model=StandardResponse[dict])
async def verify_token(
        token: str
) -> StandardResponse[dict]:
    """
    Verify a token and return user information.
    """
    try:
        # Decode the token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        # Get expiration time
        exp = payload.get("exp")
        if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
            )

        return StandardResponse(
            response_code="token_valid",
            response_detail="Token is valid",
            response_data={"username": username}
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )