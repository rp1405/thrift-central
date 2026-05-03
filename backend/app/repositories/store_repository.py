from typing import Optional

from beanie import PydanticObjectId

from app.models.store import Store


class StoreRepository:

    @staticmethod
    async def get_by_id(store_id: PydanticObjectId) -> Optional[Store]:
        return await Store.get(store_id)

    @staticmethod
    async def get_by_instagram_id(instagram_user_id: str) -> Optional[Store]:
        # Using raw MongoDB query dict because Beanie 2.x dot-notation field
        # expressions are unreliable for nested BaseModel (non-Document) fields.
        return await Store.find_one(
            {"instagram.instagram_user_id": instagram_user_id}
        )

    @staticmethod
    async def create(store: Store) -> Store:
        return await store.insert()

    @staticmethod
    async def save(store: Store) -> Store:
        return await store.save()
