from fastapi import APIRouter

from app.controllers.instagram.instagram_controller import router as instagram_router
from app.controllers.user.user_controller import router as user_router

api_router = APIRouter()

api_router.include_router(instagram_router)
api_router.include_router(user_router)
