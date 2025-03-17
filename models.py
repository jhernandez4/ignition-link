from pydantic import BaseModel
from datetime import datetime, timezone 
from .database import User, Post

class UserResponse(BaseModel):
    id: int
    username: str
    bio: str
    is_admin: bool
    profile_pic_url: str
    class Config:
        # Enable support for ORM mode
        from_attributes = True

class PostResponse(BaseModel):
    id: int
    user_id: int
    post_image_url: str
    caption: str | None
    created_at: datetime
    edited_at: datetime | None

    user: UserResponse

class VehicleResponse(BaseModel):
    id: int
    make: str
    model: str
    year: int

    class Config:
        from_attributes = True  # This allows the Pydantic model to work with SQLAlchemy models

class BuildResponse(BaseModel):
    id: int
    user_id: int
    vehicle_id: int 
    nickname: str | None 
    cover_picture_url: str
    description: str 
    vehicle: VehicleResponse

    class Config:
        from_attributes = True