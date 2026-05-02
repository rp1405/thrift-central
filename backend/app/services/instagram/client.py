from urllib.parse import urlencode

import httpx
from fastapi import HTTPException

from app.core.config import settings

INSTAGRAM_AUTH_BASE = "https://www.instagram.com/oauth/authorize"
INSTAGRAM_TOKEN_URL = "https://api.instagram.com/oauth/access_token"
GRAPH_BASE = "https://graph.instagram.com"
FB_GRAPH_BASE = "https://graph.facebook.com"


class InstagramClient:
    """Raw wrapper around the Instagram Business Login API."""

    def get_oauth_url(self) -> str:
        params = {
            "client_id": settings.INSTAGRAM_APP_ID,
            "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
            "response_type": "code",
            "scope": "pages_show_list,pages_messaging,instagram_basic,instagram_manage_messages,pages_read_engagement",
        }
        return f"https://www.facebook.com/v25.0/dialog/oauth?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> dict:
        """Exchange auth code for a short-lived access token."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FB_GRAPH_BASE}/v25.0/oauth/access_token",
                params={
                    "client_id": settings.INSTAGRAM_APP_ID,
                    "client_secret": settings.INSTAGRAM_APP_SECRET,
                    "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
                    "code": code,
                },
            )
            if not response.is_success:
                raise HTTPException(
                    status_code=400,
                    detail=f"Facebook token exchange failed: {response.text}"
                )
            return response.json()

    async def get_long_lived_token(self, short_lived_token: str) -> dict:
        """Exchange short-lived token for a long-lived token (60 days)."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FB_GRAPH_BASE}/v25.0/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": settings.INSTAGRAM_APP_ID,
                    "client_secret": settings.INSTAGRAM_APP_SECRET,
                    "fb_exchange_token": short_lived_token,
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_linked_instagram_account(self, page_id: str, page_access_token: str) -> dict:
        """Get the linked Instagram business account for a Facebook Page."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FB_GRAPH_BASE}/v25.0/{page_id}",
                params={
                    "fields": "instagram_business_account",
                    "access_token": page_access_token,
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_instagram_user_info(self, ig_id: str, page_access_token: str) -> dict:
        """Get the Instagram business account info."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FB_GRAPH_BASE}/v25.0/{ig_id}",
                params={
                    "fields": "id,username,name",
                    "access_token": page_access_token,
                },
            )
            response.raise_for_status()
            return response.json()

    async def send_message(self, page_access_token: str, recipient_id: str, message_text: str) -> dict:
        """Send a message to an Instagram user."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{FB_GRAPH_BASE}/v25.0/me/messages",
                params={
                    "access_token": page_access_token
                },
                json={
                    "messaging_type": "RESPONSE",
                    "recipient": {"id": recipient_id},
                    "message": {"text": message_text}
                }
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise HTTPException(status_code=exc.response.status_code, detail=f"Instagram API Error: {exc.response.text}")
            return response.json()

    async def get_page_accounts(self, access_token: str) -> dict:
        """Get the Facebook Pages connected to the user."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FB_GRAPH_BASE}/v25.0/me/accounts",
                params={
                    "access_token": access_token,
                },
            )
            response.raise_for_status()
            return response.json()

    async def subscribe_webhook(self, page_access_token: str, page_id: str) -> dict:
        """Subscribe app to Instagram webhooks via the connected Facebook Page."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{FB_GRAPH_BASE}/v25.0/{page_id}/subscribed_apps",
                params={
                    "subscribed_fields": "messages",
                    "access_token": page_access_token
                }
            )
            response.raise_for_status()
            return response.json()


instagram_client = InstagramClient()


