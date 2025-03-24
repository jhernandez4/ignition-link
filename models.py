from pydantic import BaseModel
from datetime import datetime, timezone 
from .database import User, Post, Brand, PartType 

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
    description: str | None

    vehicle: VehicleResponse
    owner: UserResponse

class PartResponse(BaseModel):
    id: int 
    brand_id: int
    type_id: int
    submitted_by_id: int
    part_name: str
    part_number: str 
    image_url: str
    is_verified: bool
    description: str
    created_at: datetime 

    brand: Brand
    part_type: PartType
    submitted_by: UserResponse