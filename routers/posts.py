from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import Annotated
from sqlmodel import select, Session
from pydantic import BaseModel
from datetime import datetime, timezone 
from ..database import Post
from ..dependencies import (
    get_session, get_user_from_cookie, encode_model_to_json
)

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUserDep = Annotated[Session, Depends(get_user_from_cookie)]

class CreatePostRequest(BaseModel):
    post_image_url: str
    caption: str | None = None

@router.post("")
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

class EditPostRequest(BaseModel):
    caption: str

@router.put("/{post_id}")
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

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Post edited successfully!",
            "post": encode_model_to_json(post_to_edit)
        }
    )

@router.get("/{post_id}")
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
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Post retrieved successfully!",
            "post": encode_model_to_json(post)
        }
    )

@router.get("")
def get_all_posts(
    session: SessionDep,
    offset: int = 0,
    # Less than or equal to 100; default to 100
    limit: Annotated[int, Query(le=100)] = 100,
):
    all_posts = session.exec(
        select(Post)
        .offset(offset)
        .limit(limit)
    ).all()

    if all_posts is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No posts found"
        )
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content= {
            "message": f"Successfully found {len(all_posts)} post(s)",
            "content": [
                encode_model_to_json(post)
                for post in all_posts
            ]
        }
    )

@router.get("")
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
        .offset(offset)
        .limit(limit)
    ).all()

    if posts_from_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No posts found from user with ID {user_id}"
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": f"Successfully retrieved {len(posts_from_user)} post(s) from user with ID {user_id}",
            "posts": [encode_model_to_json(post) for post in posts_from_user] 
        }
    )