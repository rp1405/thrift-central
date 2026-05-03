from typing import Optional, List

from beanie import PydanticObjectId

from app.models.item import Item


class ItemRepository:

    @staticmethod
    async def get_by_id(item_id: PydanticObjectId) -> Optional[Item]:
        return await Item.get(item_id)

    @staticmethod
    async def get_all_by_store_id(store_id: PydanticObjectId) -> List[Item]:
        # Finds all items associated with a specific store_id and returns them as a list
        return await Item.find(
            {"store_id": store_id}
        ).to_list()

    @staticmethod
    async def create(item: Item) -> Item:
        return await item.insert()

    @staticmethod
    async def save(item: Item) -> Item:
        return await item.save()