
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import Annotated
from sqlmodel import select, Session, func
from ..database import User, Like, Post
from ..models import LikeResponse
from ..dependencies import (
    get_session, get_user_from_cookie, encode_model_to_json, check_resource_exists
)

router = APIRouter(
    prefix="/likes",
    tags=["likes"]
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUserDep = Annotated[User, Depends(get_user_from_cookie)]

# Allow users to like posts
@router.post("/{post_id}", response_model=LikeResponse)
def add_like_to_post(
    post_id: int,
    session: SessionDep,
    current_user: CurrentUserDep
):
    # Check if post exists before trying to like it
    check_resource_exists(session, Post, post_id, "Post")

    existing_like = session.exec(
        select(Like).where(Like.post_id == post_id, Like.user_id == current_user.id)
    ).first()

    if existing_like:
        raise HTTPException(status_code=400, detail="Post already liked")

    new_like = Like(
        post_id=post_id,
        user_id=current_user.id
    )

    session.add(new_like)
    session.commit()
    session.refresh(new_like)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": "Post successfully liked",
            "like": encode_model_to_json(new_like)
        }
    )

@router.delete("/{post_id}")
def unlike_post(
    post_id: int,
    session: SessionDep,
    current_user: CurrentUserDep
):
    # Check if post exists before trying to unlike 
    check_resource_exists(session, Post, post_id, "Post")

    existing_like = session.exec(
        select(Like)
        .where(Like.post_id == post_id, Like.user_id == current_user.id)
    ).first()

    if not existing_like:
        raise HTTPException(
            status_code=400,
            detail="Like does not exist."
        )
    
    session.delete(existing_like)
    session.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Unliked post"
        }
    )

# Show all users who liked a post
@router.get("/for-post/{post_id}", response_model=list[LikeResponse])
def get_all_post_likes(
    post_id: int,
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    # Check if post exists before getting list of likes 
    check_resource_exists(session, Post, post_id, "Post")

    all_likes = session.exec(
        select(Like)
        .where(Like.post_id == post_id)
        .order_by(Like.liked_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    if all_likes is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No likes"
        )
    
    return all_likes

# Show the number of likes on a post
@router.get("/count/{post_id}")
def get_like_count(
    post_id: int,
    session: SessionDep
):
    # Check if post exists before getting like count on post 
    check_resource_exists(session, Post, post_id, "Post")

    like_count = session.exec(
        select(func.count())
        .where(Like.post_id == post_id)
    ).one()

    return{"post_id": post_id, "like_count": like_count}
