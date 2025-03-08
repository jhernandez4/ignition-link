from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Annotated
from sqlmodel import select, Session
from ..dependencies import get_session, get_user_from_cookie
from pydantic import BaseModel
from ..database import Post
from datetime import datetime, timezone 

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUserDep = Annotated[Session, Depends(get_user_from_cookie)]

# class PostResponse(BaseModel):
#     id: int
#     post_iamge_url: str
#     caption: str
#     created_at: datetime
#     edited_at: datetime | None = None
#     user_id: int


class CreatePostReqeuest(BaseModel):
    post_image_url: str
    caption: str | None = None

@router.post("")
def create_post(
    request: CreatePostReqeuest,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    new_post = Post(
        post_image_url=request.post_image_url,
        caption=request.caption,
        user_id=current_user.id
    )

    session.add(new_post)
    session.commit()
    session.refresh(new_post)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": "Post created successfully",
            "post": {
                "id": new_post.id,
                "post_image_url": new_post.post_image_url,
                "caption": new_post.caption,
                "created_at": new_post.created_at.isoformat(),
                "edited_at": new_post.edited_at.isoformat() if new_post.edited_at else None,
                "user_id": new_post.user_id
            }
        }
    )

