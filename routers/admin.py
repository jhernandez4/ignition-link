from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Annotated
from sqlmodel import select, Session
from pydantic import BaseModel
from ..database import Post, User
from ..models import PostResponse
from ..dependencies import (
    get_session, encode_model_to_json, get_current_user_is_admin
)

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUserAdminDep = Annotated[User, Depends(get_current_user_is_admin)]

@router.delete("/delete-post/{post_id}")
def delete_post_by_id(
    post_id: str,
    currentAdmin: CurrentUserAdminDep,
    session: SessionDep,
):
    post = session.exec(
        select(Post)
        .where(Post.id == post_id)
    ).first()

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No post found with id {post_id}"
        )

    session.delete(post)
    session.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": f"Successfully delete post with ID {post_id}",
        }
    )
