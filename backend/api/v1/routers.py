"""API v1 router aggregation."""
from fastapi import APIRouter
from backend.api.v1 import auth, upload, chat, docs

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(upload.router)
api_router.include_router(docs.router)
api_router.include_router(chat.router)



