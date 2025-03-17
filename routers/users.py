from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select, Session
from typing import Annotated
from sqlmodel import Session
from pydantic import BaseModel
from ..database import User
from ..models import UserResponse
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
            .where(User.username.ilike(f"%{username}%"))
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
