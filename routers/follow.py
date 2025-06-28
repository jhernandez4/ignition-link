from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import Annotated
from sqlmodel import select, Session, func
from ..database import User, Follow
from ..models import FollowResponse
from ..dependencies import (
    get_session, get_user_from_cookie, check_resource_exists
)

router = APIRouter(
    prefix="/follow",
    tags=["follow"]
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUserDep = Annotated[User, Depends(get_user_from_cookie)]

# Follow user
@router.post("/{user_id}", response_model=FollowResponse)
def follow_user(
    user_id: int,
    session: SessionDep,
    current_user: CurrentUserDep
):
    # Check if user exists before trying follow
    check_resource_exists(session, User, user_id, "User")

    if current_user.id == user_id:
        raise HTTPException(
            status_code=400, 
            detail="You cannot follow yourself."
        )
    
    already_following = session.exec(
        select(Follow).where(Follow.follower_id == current_user.id, Follow.following_id == user_id)
    ).first()

    if already_following:
        raise HTTPException(
            status_code=409,
            detail="You already follow this profile."
        )
    
    new_follow = Follow(
        follower_id=current_user.id,
        following_id=user_id
    )

    session.add(new_follow)
    session.commit()
    session.refresh(new_follow)

    return new_follow

# Unfollow users
@router.delete("/{user_id}")
def unfollow_user(
    user_id: int, 
    session: SessionDep,
    current_user: CurrentUserDep
):
    # Check if user exists before trying to unfollow
    check_resource_exists(session, User, user_id, "User")

    if current_user.id == user_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot unfollow yourself"
        )
    
    already_following = session.exec(
        select(Follow)
        .where(Follow.follower_id == current_user.id, Follow.following_id == user_id)
    ).first()

    if not already_following:
        raise HTTPException(
            status_code=400,
            detail="You do not follow this user"
        )

    session.delete(already_following)
    session.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Unfollowed profile"
        }
    )

# Show the list of a users followers
@router.get("/{user_id}", response_model=list[FollowResponse])
def get_all_followers(
    user_id: int,
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    # Check if user exists before getting list of followers 
    check_resource_exists(session, User, user_id, "User")

    all_followers = session.exec(
        select(Follow)
        .where(Follow.following_id == user_id)
        .offset(offset)
        .limit(limit)
        .order_by(Follow.followed_at.desc())
    ).all()

    if all_followers is None:
        raise HTTPException(
            status_code=400,
            detail="No followers"
        )
    return all_followers

# Show how many followers a user has
@router.get("/count/{user_id}")
def get_follower_count(
    user_id: int,
    session: SessionDep
):
    # Check if user exists before getting follow count 
    check_resource_exists(session, User, user_id, "User")

    followers = session.exec(
        select(Follow)
        .where(Follow.following_id == user_id)
    ).all()

    follower_count = len(followers)
    
    return{"user_id": user_id, "follower_count": follower_count}