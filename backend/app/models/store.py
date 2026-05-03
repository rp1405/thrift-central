from typing import Optional
from datetime import datetime

from beanie import Document
from pydantic import BaseModel, Field


class InstagramConnection(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: Optional[datetime] = None
    instagram_user_id: str
    instagram_username: Optional[str] = None
    page_id: Optional[str] = None
    page_access_token: Optional[str] = None


class Store(Document):
    name: str
    instagram: Optional[InstagramConnection] = None
    mobileNumber: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "stores"
