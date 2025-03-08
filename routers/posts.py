from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Annotated
from sqlmodel import select, Session
from ..dependencies import get_session, get_user_from_cookie, encode_model_to_json
from pydantic import BaseModel
from ..database import Post
from datetime import datetime, timezone 

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUserDep = Annotated[Session, Depends(get_user_from_cookie)]

class PostResponse(BaseModel):
    id: int
    post_iamge_url: str
    caption: str | None = None
    created_at: datetime
    edited_at: datetime | None = None
    user_id: int


class CreatePostRequest(BaseModel):
    post_image_url: str
    caption: str | None = None

@router.post("", response_model=PostResponse)
def create_post(
    request: CreatePostRequest,
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
            "post": encode_model_to_json(new_post) 
        }
    )

