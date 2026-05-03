from app.schemas.item import ItemSizeQuantityUpdate
from fastapi import APIRouter, status
from typing import List
from beanie import PydanticObjectId

from app.schemas.item import ItemCreate, ItemUpdate
from app.models.item import Item
from app.services.item_service import ItemService

router = APIRouter(prefix="/items", tags=["Items"])

@router.post("/", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_new_item(item_in: ItemCreate):
    """
    Create a new inventory item for a store.
    """
    return await ItemService.create_item(item_in)


@router.get("/{item_id}", response_model=Item)
async def get_item(item_id: PydanticObjectId):
    """
    Retrieve a specific item by its ID.
    """
    return await ItemService.get_item_by_id(item_id)


@router.get("/store/{store_id}", response_model=List[Item])
async def get_store_items(store_id: PydanticObjectId):
    """
    Retrieve all items belonging to a specific store.
    """
    return await ItemService.get_items_by_store(store_id)


@router.patch("/{item_id}", response_model=Item)
async def update_existing_item(item_id: PydanticObjectId, item_in: ItemUpdate):
    """
    Update details of an existing item.
    """
    return await ItemService.update_item(item_id, item_in)

# Add this endpoint to your items.py router
# Make sure to import ItemSizeQuantityUpdate at the top

@router.patch("/{item_id}/inventory", response_model=Item)
async def adjust_item_inventory(item_id: PydanticObjectId, update_in: ItemSizeQuantityUpdate):
    """
    Adjust the inventory count for a specific size of an item.
    - Provide a negative `quantity_change` for sales/reductions.
    - Provide a positive `quantity_change` for restocking.
    """
    return await ItemService.adjust_size_quantity(item_id, update_in)