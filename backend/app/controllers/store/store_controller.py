import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from beanie import PydanticObjectId

from app.models.store import Store, InstagramConnection
from app.repositories.store_repository import StoreRepository
import httpx
from app.core.config import settings

router = APIRouter(prefix="/store", tags=["Store"])
logger = logging.getLogger(__name__)


class CreateStoreRequest(BaseModel):
    name: str
    instagram_user_id: str
    access_token: str
    instagram_username: Optional[str] = None
    page_id: Optional[str] = None
    page_access_token: Optional[str] = None
    expires_in_seconds: int = 5184000


@router.post("/", summary="Create a sample store")
async def create_sample_store(request: CreateStoreRequest):
    """
    Creates a sample store with the provided Instagram details.
    """
    connection = InstagramConnection(
        access_token=request.access_token,
        expires_at=datetime.utcnow() + timedelta(seconds=request.expires_in_seconds),
        instagram_user_id=request.instagram_user_id,
        instagram_username=request.instagram_username,
        page_id=request.page_id,
        page_access_token=request.page_access_token,
    )
    new_store = Store(
        name=request.name,
        instagram=connection,
    )
    store = await StoreRepository.create(new_store)
    return {
        "message": "Store created successfully",
        "store_id": str(store.id),
        "instagram_user_id": request.instagram_user_id
    }


@router.post("/{store_id}/subscribe-webhook", summary="Subscribe to Instagram webhooks for a store")
async def subscribe_store_webhook(store_id: str):
    """
    Attempts to subscribe the store's Instagram account to our application's webhooks.
    Note: Depending on the Graph API configuration, this might require a Page ID
    instead of the Instagram User ID. We attempt with the Instagram User ID here.
    """
    try:
        store_oid = PydanticObjectId(store_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid store_id format.")

    store = await StoreRepository.get_by_id(store_oid)
    if not store or not store.instagram:
        raise HTTPException(status_code=404, detail="Store or Instagram connection not found.")

    page_access_token = store.instagram.page_access_token
    page_id = store.instagram.page_id

    if not page_access_token or not page_id:
        raise HTTPException(status_code=400, detail="Store does not have a linked Facebook Page.")

    from app.services.instagram.client import instagram_client

    # Use the shared client method to subscribe
    try:
        data = await instagram_client.subscribe_webhook(page_access_token, page_id)
    except Exception as e:
        logger.error(f"Failed to subscribe webhook: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to subscribe webhook: {str(e)}")

    return {
        "message": "Webhook subscription successful",
        "data": data
    }


@router.delete("/{store_id}", summary="Delete a store")
async def delete_store(store_id: str):
    """
    Deletes a store by their ID.
    """
    try:
        store_oid = PydanticObjectId(store_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid store_id format.")

    store = await StoreRepository.get_by_id(store_oid)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found.")

    await store.delete()
    return {"message": "Store deleted successfully", "store_id": store_id}
