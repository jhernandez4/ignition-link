from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import Annotated, List
from sqlmodel import select, Session, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from ..database import User, Follow
from ..models import FollowResponse
from ..dependencies import (
    get_session, get_user_from_cookie, encode_model_to_json
)

router = APIRouter(
    prefix="/follow",
    tags=["follow"]
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUserDep = Annotated[User, Depends(get_user_from_cookie)]

class CreateFollowRequest(BaseModel):
    following_id: int

    class Config:
        from_attributes = True

@router.post("")
def follow_user(
    request: CreateFollowRequest,
    session: SessionDep,
    current_user: CurrentUserDep
):
    if current_user.id == request.following_id:
        raise HTTPException(
            status_code=400, 
            detail="You can't follow yourself"
        )
    
    already_following = session.exec(
        select(Follow).where(Follow.follower_id == current_user.id, Follow.following_id == request.following_id)
    ).first()

    if already_following:
        raise HTTPException(
            status_code=409,
            detail="You already follow this profile"
        )
    
    new_follow = Follow(
        follower_id=current_user.id,
        following_id=request.following_id
    )

    session.add(new_follow)
    session.commit()
    session.refresh(new_follow)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": "Followed Profile"
        }
    )

@router.get("/{user_id}", response_model=list[FollowResponse])
def get_all_followers(
    user_id: int,
    session: SessionDep,
    offset: int = 0,
):
    all_followers = session.exec(
        select(Follow)
        .where(Follow.following_id == user_id)
        .offset(offset)
    ).all()

    if all_followers is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No followers"
        )
    return all_followers

@router.get("/count/{user_id}")
def get_follower_count(
    user_id: int,
    session: SessionDep
):
    followers = session.exec(
        select(Follow)
        .where(Follow.following_id == user_id)
    ).all()

    follower_count = len(followers)
    
    return{"user_id": user_id, "follower_count": follower_count}