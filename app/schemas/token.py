from pydantic import BaseModel

class Token(BaseModel):
    """Token schema for authentication response."""
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    """Token payload schema."""
    sub: str = None
    exp: int = None

class NonceUsed(BaseModel):
    status: str