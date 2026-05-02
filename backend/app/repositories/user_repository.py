from typing import Optional

from beanie import PydanticObjectId

from app.models.user import User


class UserRepository:

    @staticmethod
    async def get_by_id(user_id: PydanticObjectId) -> Optional[User]:
        return await User.get(user_id)

    @staticmethod
    async def get_by_instagram_id(instagram_user_id: str) -> Optional[User]:
        # Using raw MongoDB query dict because Beanie 2.x dot-notation field
        # expressions are unreliable for nested BaseModel (non-Document) fields.
        return await User.find_one(
            {"instagram.instagram_user_id": instagram_user_id}
        )

    @staticmethod
    async def create(user: User) -> User:
        return await user.insert()

    @staticmethod
    async def save(user: User) -> User:
        return await user.save()
