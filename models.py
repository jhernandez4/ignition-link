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