from fastapi import APIRouter

from app.api.endpoint import fx, generate_signature

from app.api.endpoint import auth

# Create API router for v1 endpoints
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["AUTH"])
api_router.include_router(generate_signature.router, prefix="/generate/signature", tags=["Signature"])
api_router.include_router(fx.router, prefix="/fx", tags=["FX"])