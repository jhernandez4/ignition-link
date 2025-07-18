from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated
from sqlmodel import select, Session
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from datetime import datetime, timezone 
from ..database import Post, User
from ..models import UserResponse, PostResponse
from ..dependencies import (
    get_session, get_user_from_cookie, encode_model_to_json
)

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUserDep = Annotated[User, Depends(get_user_from_cookie)]

class CreatePostRequest(BaseModel):
    post_image_url: str
    caption: str | None = None

@router.post("", response_model=PostResponse)
def create_post(
    request: CreatePostRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    if not request.post_image_url.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image URL cannot be empty"
        )

    new_post = Post(
        post_image_url=request.post_image_url,
        caption=request.caption,
        user_id=current_user.id
    )

    session.add(new_post)
    session.commit()
    session.refresh(new_post)

    return new_post

@router.get("", response_model=list[PostResponse])
def get_posts_from_user_id(
    user_id: int,
    session: SessionDep,
    offset: int = 0,
    # Less than or equal to 100; default to 100
    limit: Annotated[int, Query(le=100)] = 100,
):
    posts_from_user = session.exec(
        select(Post)
        .where(Post.user_id == user_id)
        .order_by(Post.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    if posts_from_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Posts list for user is null"
        )

    return posts_from_user

@router.get("/all", response_model=list[PostResponse])
def get_all_posts(
    session: SessionDep,
    offset: int = 0,
    # Less than or equal to 100; default to 100
    limit: Annotated[int, Query(le=100)] = 100,
):
    all_posts = session.exec(
        select(Post)
        .where(Post.user_id == User.id)
        .order_by(Post.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    if all_posts is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Posts list for user is null"
        )
    
    return all_posts

class EditPostRequest(BaseModel):
    caption: str

@router.put("/{post_id}", response_model=list[PostResponse])
def edit_post(
    request: EditPostRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
    post_id: int
):
    post_to_edit = session.exec(
        select(Post)
        .where(Post.id == post_id)
    ).first()

    if post_to_edit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No post found with the ID {post_id}"
        )
    if post_to_edit.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit this post."
        )
    
    post_to_edit.caption = request.caption
    post_to_edit.edited_at = datetime.now(timezone.utc)

    session.add(post_to_edit)
    session.commit()
    session.refresh(post_to_edit)

@router.get("/{post_id}", response_model=PostResponse)
def get_post_by_id(post_id: int, session: SessionDep):
    post = session.exec(
        select(Post)
        .where(Post.id == post_id)
    ).first()

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No post found with the ID {post_id}"
        )
    
    return post