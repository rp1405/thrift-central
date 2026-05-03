from datetime import datetime, timedelta
from typing import Optional

from beanie import PydanticObjectId
from fastapi import HTTPException

from app.models.store import Store, InstagramConnection
from app.repositories.store_repository import StoreRepository
from app.services.instagram.client import instagram_client


class InstagramService:

    async def get_oauth_url(self) -> str:
        return instagram_client.get_oauth_url()

    async def handle_oauth_callback(self, code: str, store_id: Optional[str] = None) -> Store:
        # Step 1: Exchange auth code for a short-lived token
        token_data = await instagram_client.exchange_code_for_token(code)
        short_lived_token = token_data.get("access_token")
        if not short_lived_token:
            raise HTTPException(status_code=400, detail=f"Token exchange failed: {token_data}")

        # Step 2: Exchange for a long-lived token (~60 days)
        long_lived_data = await instagram_client.get_long_lived_token(short_lived_token)
        access_token = long_lived_data.get("access_token")
        expires_in = long_lived_data.get("expires_in", 5_184_000)  # 60 days default
        if not access_token:
            raise HTTPException(status_code=400, detail=f"Long-lived token exchange failed: {long_lived_data}")

        # Step 3: Get Page Accounts
        try:
            accounts_data = await instagram_client.get_page_accounts(access_token)
            pages = accounts_data.get("data", [])
            if not pages:
                raise ValueError("No connected Facebook Pages found.")
            
            page_id = None
            page_access_token = None
            instagram_id = None
            
            for page in pages:
                p_id = page.get("id")
                p_token = page.get("access_token")
                
                # Step 4: Get linked Instagram account
                ig_data = await instagram_client.get_linked_instagram_account(p_id, p_token)
                ig_account = ig_data.get("instagram_business_account")
                
                if ig_account and ig_account.get("id"):
                    page_id = p_id
                    page_access_token = p_token
                    instagram_id = ig_account.get("id")
                    break

            if not instagram_id:
                raise ValueError("No Instagram Business Account linked to any of the Facebook Pages.")

            # Step 5: Get Instagram user info
            ig_info = await instagram_client.get_instagram_user_info(instagram_id, page_access_token)
            instagram_username = ig_info.get("username", "Unknown")
            instagram_name = ig_info.get("name") or instagram_username

            # Step 6: Subscribe to webhooks via the Page
            await instagram_client.subscribe_webhook(page_access_token, page_id)
            
            connection = InstagramConnection(
                access_token=access_token,
                expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
                instagram_user_id=instagram_id,
                instagram_username=instagram_username,
                page_id=page_id,
                page_access_token=page_access_token,
            )
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to setup page or subscribe webhook: {e}")
            print(f"FAILED TO GET PAGE ACCOUNTS: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to connect Instagram account: {e}")

        # Step 7: Attach to existing store or create new one
        if store_id:
            store = await StoreRepository.get_by_id(PydanticObjectId(store_id))
            if store:
                store.instagram = connection
                store.updated_at = datetime.utcnow()
                return await StoreRepository.save(store)

        existing = await StoreRepository.get_by_instagram_id(instagram_id)
        if existing:
            existing.instagram = connection
            existing.updated_at = datetime.utcnow()
            return await StoreRepository.save(existing)

        new_store = Store(
            name=instagram_name,
            instagram=connection,
        )
        return await StoreRepository.create(new_store)

    async def send_message(self, store_id: str, recipient_id: str, message_text: str) -> dict:
        """Send a message to an Instagram user from the backend."""
        store = await StoreRepository.get_by_id(PydanticObjectId(store_id))
        if not store or not store.instagram or not store.instagram.page_access_token:
            raise HTTPException(status_code=400, detail="Store does not have a valid Instagram page connection.")
            
        return await instagram_client.send_message(
            page_access_token=store.instagram.page_access_token,
            recipient_id=recipient_id,
            message_text=message_text
        )


instagram_service = InstagramService()
