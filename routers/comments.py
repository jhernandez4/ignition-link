from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import Annotated
from sqlmodel import select, Session
from pydantic import BaseModel
from ..database import User, Comment, Post
from ..models import CommentResponse
from ..dependencies import (
    get_session, get_user_from_cookie, encode_model_to_json, check_resource_exists
)

router = APIRouter(
    prefix="/comments",
    tags=["comments"]
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUserDep = Annotated[User, Depends(get_user_from_cookie)]

class CreateCommentRequest(BaseModel):
    post_id: int
    comment: str

# Allow users to comment on posts
@router.post("", response_model=CommentResponse)
def create_comment_on_post(
    request: CreateCommentRequest,
    session: SessionDep,
    current_user: CurrentUserDep
):
    # Check if post exists before trying to comment on it
    check_resource_exists(session, Post, request.post_id, "Post")

    new_comment = Comment(
        post_id=request.post_id,
        comment=request.comment,
        user_id=current_user.id
    )

    session.add(new_comment)
    session.commit()
    session.refresh(new_comment)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": "Comment added successfully",
            "comment": encode_model_to_json(new_comment)
        }
    )

@router.delete("/{comment_id}")
def delete_comment_on_post(
    comment_id: int,
    session: SessionDep,
    current_user: CurrentUserDep
):
    new_comment = session.exec(
        select(Comment)
        .where(
            Comment.id == comment_id, Comment.user_id == current_user.id
        )
    ).first()

    if not new_comment:
        raise HTTPException(
            status_code=400,
            detail="Comment does not exist."
        )
    
    session.delete(new_comment)
    session.commit()
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Comment deleted."
        }
    )

# Show the comments on a post
@router.get("", response_model=list[CommentResponse])
def get_all_post_comments(
    post_id: int,
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    # Check if post exists before trying to get its list of comments 
    check_resource_exists(session, Post, post_id, "Post")

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