import logging
from datetime import datetime

from app.repositories.user_repository import UserRepository
from app.schemas.instagram import InstagramWebhookPayload, WebhookMessaging
from app.services.instagram.client import instagram_client

logger = logging.getLogger(__name__)


class WebhookHandler:

    async def handle(self, payload: InstagramWebhookPayload) -> None:
        if payload.object != "instagram":
            logger.warning(f"Unexpected webhook object type: {payload.object}")
            return

        for entry in payload.entry:
            for messaging_event in entry.messaging:
                await self._process_messaging_event(
                    business_instagram_id=entry.id,
                    event=messaging_event,
                )

    async def _process_messaging_event(
        self,
        business_instagram_id: str,
        event: WebhookMessaging,
    ) -> None:
        # Only process actual messages (not read receipts, delivery events, etc.)
        if not event.message:
            return

        sender_id = event.sender.id
        recipient_id = event.recipient.id

        # Figure out who is the customer and who is the business
        is_customer_sending = recipient_id == business_instagram_id
        customer_id = sender_id if is_customer_sending else recipient_id
        sender_type = "customer" if is_customer_sending else "business"

        # Find the business owner (User) this webhook is for
        user = await UserRepository.get_by_instagram_id(business_instagram_id)
        if not user:
            logger.warning(f"Webhook received for unknown Instagram account: {business_instagram_id}")
            return

        # Just log the message instead of storing it
        logger.info(f"Received message from {sender_type} ({sender_id}): {event.message.text}")

        # Echo the message back if it's from the customer
        if is_customer_sending and event.message.text and user.instagram and user.instagram.page_access_token:
            try:
                await instagram_client.send_message(
                    page_access_token=user.instagram.page_access_token,
                    recipient_id=customer_id,
                    message_text=event.message.text + " - Thrift Central"
                )
                logger.info(f"Echoed message back to customer {customer_id}")
            except Exception as e:
                logger.error(f"Failed to echo message: {e}")


webhook_handler = WebhookHandler()
