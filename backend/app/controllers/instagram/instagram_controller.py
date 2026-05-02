import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request, BackgroundTasks
from fastapi.responses import PlainTextResponse

from pydantic import BaseModel
from beanie import PydanticObjectId


from app.core.config import settings
from app.schemas.instagram import InstagramWebhookPayload
from app.services.instagram.instagram_service import instagram_service
from app.services.instagram.webhook_handler import webhook_handler

router = APIRouter(prefix="/instagram", tags=["Instagram"])
logger = logging.getLogger(__name__)


@router.get("/auth", summary="Start Instagram OAuth flow")
async def instagram_auth(user_id: Optional[str] = Query(default=None)):
    """
    Redirect the business owner to Instagram's OAuth consent screen.
    Optionally pass ?user_id=<id> to attach the Instagram account to an existing user.
    """
    url = await instagram_service.get_oauth_url()
    # In a real frontend flow this would be a RedirectResponse.
    # Returning the URL so the frontend can handle the redirect.
    return {"auth_url": url}


@router.get("/callback", summary="Handle Instagram OAuth callback")
async def instagram_callback(
    code: str = Query(...),
    user_id: Optional[str] = Query(default=None),
):
    """
    Instagram redirects here after the user grants permissions.
    Exchanges the code for tokens and stores them on the User document.
    """
    user = await instagram_service.handle_oauth_callback(code=code, user_id=user_id)
    return {
        "message": "Instagram account connected successfully.",
        "user_id": str(user.id),
        "instagram_username": user.instagram.instagram_username if user.instagram else None,
    }


@router.get("/webhook", summary="Verify webhook with Meta", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
):
    """
    Meta calls this GET endpoint to verify our webhook URL.
    We must echo back hub.challenge if the verify token matches.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.INSTAGRAM_WEBHOOK_VERIFY_TOKEN:
        logger.info("Webhook verification successful.")
        return hub_challenge

    logger.warning("Webhook verification failed — token mismatch.")
    raise HTTPException(status_code=403, detail="Webhook verification failed.")


@router.post("/webhook", summary="Receive Instagram DM events")
async def receive_webhook(payload: InstagramWebhookPayload, background_tasks: BackgroundTasks):
    """
    Meta sends real-time DM events here.
    We parse and process each message in the background to respond to Meta immediately.
    """
    # print(f"Received webhook payload:\n{payload.model_dump_json(indent=2)}")
    print("Received message==================================  \n\n", payload.entry[0].messaging[0].message.text)
    print("\n\n==================================================")
    background_tasks.add_task(webhook_handler.handle, payload)
    return {"status": "ok"}


@router.get("/send-message", summary="Send an Instagram message")
async def send_message(user_id: str, recipient_id: str, message_text: str):
    """
    Send a message from the authenticated user's Instagram account.
    """
    try:
        # basic validation that user_id is objectid
        PydanticObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id format.")

    result = await instagram_service.send_message(
        user_id=user_id,
        recipient_id=recipient_id,
        message_text=message_text
    )
    return result
