"""
API routers.
"""

from fastapi import APIRouter

from piggy.api.v1 import api_v1_router

api_router = APIRouter(prefix="/api")
api_router.include_router(api_v1_router)
