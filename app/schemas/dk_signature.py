# app/schemas/dk_signature.py
from pydantic import BaseModel, Field
from typing import Dict, Any

class ReqDKSignature(BaseModel):
    request_body: Dict[str, Any]
    nonce: str
    timestamp: str
    
class DKSignatreResponse(BaseModel):
    dk_signature: str
    type: str