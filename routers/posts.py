from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from sqlmodel import select, Session
from ..dependencies import get_session, get_user_from_cookie
from pydantic import BaseModel

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUserDep = Annotated[Session, Depends(get_user_from_cookie)]


class CreatePostReqeuest(BaseModel):
    post_image_url: str
    caption: str | None = None

# @router.post("")
# def create_post(
#     current_user: CurrentUserDep,
#     session: SessionDep,
# ):
    