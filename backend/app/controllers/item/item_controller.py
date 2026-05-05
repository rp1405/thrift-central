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

@router.post(
    "/bulk", 
    response_model=List[Item],
    status_code=status.HTTP_201_CREATED,
    summary="Create multiple items"
)
async def create_multiple_items(items_in: List[ItemCreate]):
    """
    Uploads a batch of items to the inventory. 
    Automatically assigns unique, store-specific item codes (e.g., AB-1234) to each item.
    """
    created_items = await ItemService.create_items_bulk(items_in)
    return created_items


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


@router.get("/store/{store_id}/code/{code}", response_model=Item)
async def get_item_by_store_and_code(store_id: PydanticObjectId, code: str):
    """
    Retrieve a specific item using its store ID and unique item code (e.g., AB-1234).
    """
    return await ItemService.get_item_by_code(store_id, code)


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