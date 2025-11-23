from fastapi import APIRouter

from app.api.v1.endpoints import chat, housing


api_router = APIRouter()

# Chat / LLM endpoints
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])

# Housing endpoints
api_router.include_router(housing.router, prefix="/housing", tags=["housing"])
