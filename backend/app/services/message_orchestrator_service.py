# app/services/message_orchestrator.py
import re
from fastapi import HTTPException
from app.services.item_service import ItemService
from app.repositories.store_repository import StoreRepository
from app.models.store import Store
from app.services.instagram.client import instagram_client

class MessageOrchestratorService:

    FAILURE_MESSAGE = "I couldn't find any item codes in your message. Please use the format: XX-0000"
    GREETING_MESSAGE = "Thank you for reaching out to {store_name}.\n\n"
    
    @staticmethod
    async def execute_action(
        store: Store,
        sender_id: str,
        message: str,
    ) -> None:
        # 1. Extract the codes
        codes = await MessageOrchestratorService.parse_command(message)
        
        # 2. If no codes found, send failure message
        if not codes:
            await instagram_client.send_message(
                store.instagram.page_access_token, 
                sender_id, 
                MessageOrchestratorService.FAILURE_MESSAGE
            )
            return
        
        # 3. Verify the codes and get the items
        try:
            items = await ItemService.get_items_by_store_and_codes(
                store_id=store.id,
                codes=codes
            )
        except HTTPException as e:
            # If the user asked for AB-1234 but it doesn't exist, send the 404 detail string
            await instagram_client.send_message(
                store.instagram.page_access_token, 
                sender_id, 
                e.detail
            )
            return

        # 4. Build the successful confirmation message
        # Format the greeting with the specific store's name
        greeting = MessageOrchestratorService.GREETING_MESSAGE.format(store_name=store.name)
        response_lines = [f"{greeting}✨ Got it! Here is what you requested:\n"]
        total_price = 0
        
        for item in items:
            response_lines.append(f"• {item.code}: {item.name} - ₹{item.price}")
            total_price += item.price
            
        response_lines.append(f"\n🛒 Total: ₹{total_price}")
        response_lines.append("\nReply 'CONFIRM' to reserve these items before they sell out!")
        
        final_message = "\n".join(response_lines)
        
        # 5. Send the final response back to the DM
        await instagram_client.send_message(
            store.instagram.page_access_token, 
            sender_id, 
            final_message
        )

    @staticmethod
    async def parse_command(message: str) -> list[str]:
        """
        Parses a message to extract item codes matching the pattern XX-0000.
        """
        pattern = r'[a-zA-Z]{2}-[\w]{4}'
        extracted_codes = re.findall(pattern, message)
        
        normalized_codes = [code.upper() for code in extracted_codes]
        unique_codes = list(set(normalized_codes))
        
        return unique_codes