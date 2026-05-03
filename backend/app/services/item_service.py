from app.schemas.item import ItemSizeQuantityUpdate
from typing import List
from beanie import PydanticObjectId
from fastapi import HTTPException, status
from datetime import datetime

from app.models.item import Item
from app.repositories.item_repository import ItemRepository
from app.schemas.item import ItemCreate, ItemUpdate

class ItemService:

    @staticmethod
    async def create_item(item_data: ItemCreate) -> Item:
        # Convert the Pydantic schema to a Beanie Document
        item = Item(**item_data.model_dump())
        return await ItemRepository.create(item)

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