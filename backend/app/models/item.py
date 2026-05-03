from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from enum import Enum

class ItemSize(str, Enum):
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"
    XXL = "XXL"
    XXXL = "XXXL"
    ONE_SIZE = "ONE_SIZE"


class Item(Document):
    name: str
    price: float
    description: str
    images: list[str]
    store_id: PydanticObjectId
    sizeCount:dict[ItemSize, int]

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "items"