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
async def instagram_auth(store_id: Optional[str] = Query(default=None)):
    """
    Redirect the business owner to Instagram's OAuth consent screen.
    Optionally pass ?store_id=<id> to attach the Instagram account to an existing store.
    """
    url = await instagram_service.get_oauth_url()
    # In a real frontend flow this would be a RedirectResponse.
    # Returning the URL so the frontend can handle the redirect.
    return {"auth_url": url}


@router.get("/callback", summary="Handle Instagram OAuth callback")
async def instagram_callback(
    code: str = Query(...),
    store_id: Optional[str] = Query(default=None),
):
    """
    Instagram redirects here after the user grants permissions.
    Exchanges the code for tokens and stores them on the Store document.
    """
    store = await instagram_service.handle_oauth_callback(code=code, store_id=store_id)
    return {
        "message": "Instagram account connected successfully.",
        "store_id": str(store.id),
        "instagram_username": store.instagram.instagram_username if store.instagram else None,
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
async def send_message(store_id: str, recipient_id: str, message_text: str):
    """
    Send a message from the authenticated store's Instagram account.
    """
    try:
        # basic validation that store_id is objectid
        PydanticObjectId(store_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid store_id format.")

    result = await instagram_service.send_message(
        store_id=store_id,
        recipient_id=recipient_id,
        message_text=message_text
    )
    return result
