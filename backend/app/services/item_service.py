from app.schemas.item import ItemSizeQuantityUpdate
from typing import List
from beanie import PydanticObjectId
from fastapi import HTTPException, status
from datetime import datetime

from app.models.item import Item
from app.repositories.item_repository import ItemRepository
from app.repositories.store_repository import StoreRepository
from app.schemas.item import ItemCreate, ItemUpdate
from pymongo.errors import DuplicateKeyError
import string
import random

class ItemService:

    @staticmethod
    def _generate_item_code(store_name: str) -> str:
        """Helper method to generate the AB-1234 format code"""
        # 1. Determine Prefix
        words = store_name.strip().split()
        if len(words) >= 2:
            # First letters of the first two words
            prefix = (words[0][0] + words[1][0]).upper()
        else:
            # First and second letter of a single word
            name = words[0]
            if len(name) >= 2:
                prefix = name[:2].upper()
            else:
                # Edge case: Store name is only 1 letter
                prefix = (name[0] + "X").upper() 

        # 2. Determine Suffix (4 alphanumeric chars, uppercase)
        charset = string.ascii_uppercase + string.digits
        suffix = ''.join(random.choices(charset, k=4))

        return f"{prefix}-{suffix}"
    
    @staticmethod
    async def create_items_bulk(items_data: List[ItemCreate]) -> List[Item]:
        # 1. Fetch all required stores in a single query to avoid N+1 DB hits
        store_ids = list(set([item.store_id for item in items_data]))
        stores = await StoreRepository.get_by_ids(store_ids)
        
        # Map store ID to the store object for instant lookups
        store_map = {store.id: store for store in stores}
        
        # Validate that all requested stores actually exist
        if len(stores) != len(store_ids):
             raise HTTPException(
                 status_code=status.HTTP_404_NOT_FOUND, 
                 detail="One or more stores provided in the batch do not exist."
             )

        max_retries = 3
        for attempt in range(max_retries):
            items_to_insert = []
            generated_codes_set = set()
            
            for item_data in items_data:
                store = store_map[item_data.store_id]
                item_dict = item_data.model_dump()
                
                # 2. Generate a code and ensure it's unique WITHIN this specific batch
                # (Prevents generating the same code twice in the same millisecond)
                while True:
                    code = ItemService._generate_item_code(store.name)
                    unique_key = f"{store.id}_{code}"
                    
                    if unique_key not in generated_codes_set:
                        generated_codes_set.add(unique_key)
                        item_dict["code"] = code
                        break
                        
                items_to_insert.append(Item(**item_dict))
                
            try:
                # 3. Perform a single bulk insert operation
                return await ItemRepository.create_many(items_to_insert)
            
            except DuplicateKeyError:
                # If the DB rejects the batch due to a collision with an OLD item,
                # we catch it and regenerate all codes for this batch on the next loop.
                if attempt == max_retries - 1:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to generate unique item codes for the batch after multiple attempts."
                    )
                continue

    @staticmethod
    async def get_item_by_id(item_id: PydanticObjectId) -> Item:
        item = await ItemRepository.get_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with id {item_id} not found."
            )
        return item

    @staticmethod
    async def get_items_by_store(store_id: PydanticObjectId) -> List[Item]:
        return await ItemRepository.get_all_by_store_id(store_id)

    @staticmethod
    async def get_item_by_code(store_id: PydanticObjectId, code: str) -> Item:
        item = await ItemRepository.get_by_store_and_code(store_id, code)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with code '{code}' not found in this store."
            )
        return item
    
    @staticmethod
    async def get_items_by_store_and_codes(
        store_id: PydanticObjectId, 
        codes: List[str]
    ) -> List[Item]:
        
        # 1. Deduplicate the codes (just in case they weren't cleaned earlier)
        unique_codes = list(set(codes))
        
        # 2. Fetch all matching items in one go
        items = await ItemRepository.get_by_store_and_codes(store_id, unique_codes)
        
        # 3. Strict Validation: Identify if any codes were invalid
        if len(items) != len(unique_codes):
            # Extract the codes that were successfully found
            found_codes = {item.code for item in items}
            
            # Figure out exactly which ones are missing
            missing_codes = [code for code in unique_codes if code not in found_codes]
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"The following item codes were not found in this store: {', '.join(missing_codes)}"
            )
            
        return items

    @staticmethod
    async def update_item(item_id: PydanticObjectId, update_data: ItemUpdate) -> Item:
        item = await ItemService.get_item_by_id(item_id)
        
        # Only update fields that were actually provided in the request
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for key, value in update_dict.items():
            setattr(item, key, value)
            
        item.updated_at = datetime.utcnow()
        return await ItemRepository.save(item)
    
    # Add this method inside your ItemService class

    @staticmethod
    async def adjust_size_quantity(item_id: PydanticObjectId, size_update: ItemSizeQuantityUpdate) -> Item:
        item = await ItemService.get_item_by_id(item_id)
        
        # Get the current quantity (default to 0 if the size isn't in the dict yet)
        current_quantity = item.sizeCount.get(size_update.size, 0)
        
        # Calculate the new quantity
        new_quantity = current_quantity + size_update.quantity_change
        
        # Prevent negative inventory
        if new_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for size {size_update.size.value}. Current stock: {current_quantity}."
            )
            
        # Update the specific size count
        item.sizeCount[size_update.size] = new_quantity
        item.updated_at = datetime.utcnow()
        
        return await ItemRepository.save(item)