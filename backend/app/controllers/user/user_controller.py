import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from beanie import PydanticObjectId

from app.models.user import User, InstagramConnection
from app.repositories.user_repository import UserRepository
import httpx
from app.core.config import settings

router = APIRouter(prefix="/user", tags=["User"])
logger = logging.getLogger(__name__)


class CreateUserRequest(BaseModel):
    name: str
    instagram_user_id: str
    access_token: str
    instagram_username: Optional[str] = None
    page_id: Optional[str] = None
    page_access_token: Optional[str] = None
    expires_in_seconds: int = 5184000


@router.post("/", summary="Create a sample user")
async def create_sample_user(request: CreateUserRequest):
    """
    Creates a sample user with the provided Instagram details.
    """
    connection = InstagramConnection(
        access_token=request.access_token,
        expires_at=datetime.utcnow() + timedelta(seconds=request.expires_in_seconds),
        instagram_user_id=request.instagram_user_id,
        instagram_username=request.instagram_username,
        page_id=request.page_id,
        page_access_token=request.page_access_token,
    )
    new_user = User(
        name=request.name,
        instagram=connection,
    )
    user = await UserRepository.create(new_user)
    return {
        "message": "User created successfully",
        "user_id": str(user.id),
        "instagram_user_id": request.instagram_user_id
    }


@router.post("/{user_id}/subscribe-webhook", summary="Subscribe to Instagram webhooks for a user")
async def subscribe_user_webhook(user_id: str):
    """
    Attempts to subscribe the user's Instagram account to our application's webhooks.
    Note: Depending on the Graph API configuration, this might require a Page ID 
    instead of the Instagram User ID. We attempt with the Instagram User ID here.
    """
    try:
        user_oid = PydanticObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id format.")

    user = await UserRepository.get_by_id(user_oid)
    if not user or not user.instagram:
        raise HTTPException(status_code=404, detail="User or Instagram connection not found.")

    page_access_token = user.instagram.page_access_token
    page_id = user.instagram.page_id

    if not page_access_token or not page_id:
        raise HTTPException(status_code=400, detail="User does not have a linked Facebook Page.")

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


@router.delete("/{user_id}", summary="Delete a user")
async def delete_user(user_id: str):
    """
    Deletes a user by their ID.
    """
    try:
        user_oid = PydanticObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id format.")

    user = await UserRepository.get_by_id(user_oid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    await user.delete()
    return {"message": "User deleted successfully", "user_id": user_id}
