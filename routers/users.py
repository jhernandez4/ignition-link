from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select, Session, delete, func
from typing import Annotated
from sqlmodel import Session
from pydantic import BaseModel
from ..database import User, Build, Post, Part
from ..models import UserResponse, UserWithBuildsResponse
from copy import deepcopy
from firebase_admin import auth
from ..dependencies import (
    get_session, check_username_exists, get_user_from_cookie
)

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[]
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUserDep = Annotated[User, Depends(get_user_from_cookie)]

@router.get("/me")
def read_user_me(current_user: CurrentUserDep):

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Current user found",
            # Filter out data with UserReponse model
            "user": UserResponse.model_validate(current_user).model_dump()
        }
    )

class ProfileChangeRequest(BaseModel):
    username: str | None = None
    bio: str | None = None
    profile_pic_url: str | None = None

@router.put("/me")
def edit_user_me(
    current_user: CurrentUserDep,
    request: ProfileChangeRequest,
    session: SessionDep
):
    if request.username is not None:
       username_taken = check_username_exists(request.username, session)
       if username_taken:
           raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{request.username}' is already taken"
            )

       current_user.username = request.username

    if request.bio is not None:
       current_user.bio = request.bio

    if request.profile_pic_url is not None:
        current_user.profile_pic_url = request.profile_pic_url

    try:
        # Save changes to the database
        session.add(current_user)
        session.commit()
        session.refresh(current_user)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Current user profile updated successfully",
                "user": UserResponse.model_validate(current_user).model_dump()
            }
        )
    except Exception as e:
        session.rollback()  # Rollback in case of any error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the profile"
        )

@router.delete("/me")
def delete_user_me(
    current_user: CurrentUserDep,
    session: SessionDep
):
    # Delete user from Firebase first 
    auth.delete_user(current_user.firebase_uid)

    # Delete Posts
    session.exec(
        delete(Post)
        .where(Post.user_id == current_user.id)
    )

    user_builds = session.exec(
        select(Build)
        .where(Build.user_id == current_user.id)
    ).all()

    # Remove all parts from user's builds before deleting builds
    for build in user_builds:
        build.parts.clear()

    # Delete Builds
    session.exec(
        delete(Build)
        .where(Build.user_id == current_user.id)
    )

    # Delete Part submissions
    session.exec(
        delete(Part)
        .where(Part.submitted_by_id == current_user.id)
    )

    # Delete user from database
    session.delete(current_user)
    session.commit()
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Current user successfully deleted"
        }
    )

@router.get("/query")
def get_users_by_username(
    username: str,
    session: SessionDep,
    offset: int = 0,
    # Less than or equal to 100; default to 100
    limit: Annotated[int, Query(le=100)] = 100,
):
    try:
        users = session.exec(
            select(User)
            .where(
                # User.username.ilike(f"%{username}%")
                func.similarity(User.username, username) > 0.1
            )
            .offset(offset)
            .limit(limit)
        ).all()

        if not users:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": f"No users found matching '{username}'", "data": []}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Found {len(users)} user(s) matching '{username}'",
                "users": [
                    UserResponse.model_validate(user).model_dump()
                    for user in users
                ]
            }
        )

    except SQLAlchemyError:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "An error occurred while querying the database."}
        )

@router.get("/vehicle-search", response_model=list[UserWithBuildsResponse])
def get_users_by_vehicle_owned(
    vehicle_id: int,
    session: SessionDep,
    offset: int = 0,
    # Less than or equal to 100; default to 100
    limit: Annotated[int, Query(le=100)] = 100,
):
    users = session.exec(
        select(User)
        .join(User.builds)  # Join with the builds relationship
        .where(Build.vehicle_id == vehicle_id)  # Correctly filter by vehicle_id in builds
        .offset(offset)
        .limit(limit)
    ).unique().all()

    if users is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to retrieve users. List is null"
        )
    
    # Build a new list of copied users with filtered builds
    filtered_user_copies = []
    for user in users:
        matching_builds = [b for b in user.builds if b.vehicle_id == vehicle_id]
        user_copy = deepcopy(user)
        user_copy.builds = matching_builds

        filtered_user_copies.append(user_copy)

    return filtered_user_copies

@router.get("/{user_id}")
def read_user_by_id(user_id: int, session: SessionDep):
    try:
        user = session.exec(
            select(User).where(User.id == user_id)
        ).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} does not exist"
            )

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while querying the database."
        ) from e

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": f"User with ID '{user_id}' found",
            "user": UserResponse.model_validate(user).model_dump()
        }
    )

@router.get("")
def read_user_by_username(username: str, session: SessionDep):
    try:
        user = session.exec(
            select(User).where(User.username == username)
        ).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with username {username} does not exist"
            )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while querying the database."
        ) from e

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": f"User with username '{username}' found",
            "user": UserResponse.model_validate(user).model_dump()
        }
    )
