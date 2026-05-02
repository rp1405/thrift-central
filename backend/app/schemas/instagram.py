from typing import Optional, List, Any, Dict

from pydantic import BaseModel


# ─── Webhook Payload Schemas ──────────────────────────────────────────────────

class WebhookSender(BaseModel):
    id: str


class WebhookRecipient(BaseModel):
    id: str


class WebhookMessageContent(BaseModel):
    mid: str
    text: Optional[str] = None


class WebhookMessaging(BaseModel):
    sender: WebhookSender
    recipient: WebhookRecipient
    timestamp: int
    message: Optional[WebhookMessageContent] = None


class WebhookEntry(BaseModel):
    id: str
    time: int
    messaging: List[WebhookMessaging] = []


class InstagramWebhookPayload(BaseModel):
    object: str
    entry: List[WebhookEntry]
