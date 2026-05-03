from fastapi import APIRouter

from app.controllers.instagram.instagram_controller import router as instagram_router
from app.controllers.store.store_controller import router as store_router
from app.controllers.item.item_controller import router as item_router

api_router = APIRouter()

api_router.include_router(instagram_router)
api_router.include_router(store_router)
api_router.include_router(item_router)

