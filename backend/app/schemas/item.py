from pydantic import BaseModel
from beanie import PydanticObjectId
from typing import List, Dict, Optional

# Assuming ItemSize is importable from your models file
from app.models.item import ItemSize 

class ItemCreate(BaseModel):
    name: str
    price: float
    description: str
    images: List[str] = []
    store_id: PydanticObjectId
    sizeCount: Dict[ItemSize, int]

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    images: Optional[List[str]] = None
    sizeCount: Optional[Dict[ItemSize, int]] = None

# Add this to your existing item.py schemas

class ItemSizeQuantityUpdate(BaseModel):
    size: ItemSize
    quantity_change: int 
    # Example: 
    # Use -1 when an item is sold
    # Use +50 when new stock arrives