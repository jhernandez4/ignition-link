from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import Annotated, List
from sqlmodel import select, Session, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from datetime import datetime, timezone 
from ..database import Post, User, Comment, Like
from ..models import UserResponse, PostResponse, CommentResponse, LikeResponse
from ..dependencies import (
    get_session, get_user_from_cookie, encode_model_to_json
)

router = APIRouter(
    prefix="/interactions",
    tags=["interactions"]
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUserDep = Annotated[User, Depends(get_user_from_cookie)]

class CreateCommentRequest(BaseModel):
    post_id: int
    comment: str

# Allow users to comment on posts
@router.post("/comment", response_model=CommentResponse)
def create_comment_on_post(
    request: CreateCommentRequest,
    session: SessionDep,
    current_user: CurrentUserDep
):
    new_comment = Comment(
        post_id=request.post_id,
        comment=request.comment,
        user_id=current_user.id
    )

    session.add(new_comment)
    session.commit()
    session.refresh(new_comment)

    return new_comment

@router.delete("/comment/{comment_id}")
def delete_comment_on_post(
    request: CreateCommentRequest,
    session: SessionDep,
    current_user: CurrentUserDep
):
    new_comment = session.exec(
        select(Comment)
        .where(Comment.post_id == request.post_id, Comment.comment == request.comment, Comment.user_id == current_user.id)
    ).first()

    if not new_comment:
        raise HTTPException(
            status_code=400,
            detail="No comment to delete"
        )
    
    session.delete(new_comment)
    session.commit()
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Comment Deleted"
        }
    )

class CreateLikeRequest(BaseModel):
    post_id: int

# Allow users to like posts
@router.post("/like", response_model=LikeResponse)
def add_like_to_post(
    request: CreateLikeRequest,
    session: SessionDep,
    current_user: CurrentUserDep
):
    existing_like = session.exec(
        select(Like)
        .where(Like.post_id == request.post_id, Like.user_id == current_user.id)
    ).first()

    if existing_like:
        raise HTTPException(
            status_code=400, 
            detail="Post already liked")

    new_like = Like(
        post_id=request.post_id,
        user_id=current_user.id
    )

    session.add(new_like)
    session.commit()
    session.refresh(new_like)

    return new_like

@router.delete("/like")
def unlike_a_post(
    request: CreateLikeRequest,
    session: SessionDep,
    current_user: CurrentUserDep
):
    existing_like = session.exec(
        select(Like)
        .where(Like.post_id == request.post_id, Like.user_id == current_user.id)
    ).first()

    if not existing_like:
        raise HTTPException(
            status_code=400,
            detail="You haven't liked this post"
        )
    
    session.delete(existing_like)
    session.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Unliked Post"
        }
    )


# Show the comments on a post
@router.get("/comments/{post_id}", response_model=list[CommentResponse])
def get_all_post_comments(
    post_id: int,
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    all_comments = session.exec(
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    if all_comments is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No comments"
        )
    
    return all_comments

# Show who liked a post
@router.get("/likes/{post_id}", response_model=list[LikeResponse])
def get_all_post_likes(
    post_id: int,
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    all_likes = session.exec(
        select(Like)
        .where(Like.post_id == post_id)
        .order_by(Like.created_at.desc())
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
@router.get("/likes/count/{post_id}")
def get_like_count(
    post_id: int,
    session: SessionDep
):
    likes = session.exec(
        select(Like)
        .where(Like.post_id == post_id)
    ).all()

    like_count = len(likes)

    return{"post_id": post_id, "like_count": like_count}
