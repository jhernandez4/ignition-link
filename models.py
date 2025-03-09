from pydantic import BaseModel
from datetime import datetime, timezone 

class PostResponse(BaseModel):
    id: int
    post_iamge_url: str
    caption: str | None = None
    created_at: datetime
    edited_at: datetime | None = None
    user_id: int