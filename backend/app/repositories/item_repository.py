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
    async def create_many(items: List[Item]) -> List[Item]:
        """
        Inserts multiple items into the database in one network trip.
        """
        await Item.insert_many(items)
        
        # Now the 'items' list has all the newly generated _id fields attached
        return items

    @staticmethod
    async def save(item: Item) -> Item:
        return await item.save()

    @staticmethod
    async def get_by_store_and_code(store_id: PydanticObjectId, code: str) -> Optional[Item]:
        return await Item.find_one(
            {"store_id": store_id, "code": code}
        )
    
    @staticmethod
    async def get_by_store_and_codes(
        store_id: PydanticObjectId, 
        codes: List[str]
    ) -> List[Item]:
        """
        Fetches multiple items for a specific store in a single DB trip.
        """
        # Assuming Beanie ODM syntax based on your snippet
        return await Item.find(
            {
                "store_id": store_id, 
                "code": {"$in": codes}
            }
        ).to_list()
    
    @staticmethod
    async def get_by_ids(item_ids: List[PydanticObjectId]) -> List[Item]:
        return await Item.find({"_id": {"$in": item_ids}}).to_list()