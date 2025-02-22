from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from ..dependencies import (
    get_session, verify_firebase_session_cookie, get_user_from_uid,
    check_username_exists, get_user_from_id
)
from typing import Annotated
from sqlmodel import Session
from pydantic import BaseModel

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[]
)

SessionDep = Annotated[Session, Depends(get_session)]

class UIDRequest(BaseModel):
    uid: str

@router.get("/me")
def read_user_me(request: UIDRequest, session: SessionDep):
    current_user = get_user_from_uid(request.uid, session)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Current user found",
            "data": {
                "id": current_user.id,
                "username": current_user.username,
                "bio": current_user.bio
            }
        }
    )

class ProfileChangeRequest(BaseModel):
    uid: str
    username: str | None = None
    bio: str | None = None

@router.put("/me")
def edit_user_me(request: ProfileChangeRequest, session: SessionDep):
    current_user = get_user_from_uid(request.uid, session)
    
    if request.username is not None:
       username_taken = check_username_exists(request.username, session)
       if username_taken:
           raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already taken"
            )

       current_user.username = request.username

    if request.bio is not None:
       current_user.bio = request.bio

    try:
        # Save changes to the database
        session.add(current_user)
        session.commit()
        session.refresh(current_user)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Current user profile updated successfully",
                "data": {
                    "id": current_user.id,
                    "username": current_user.username,
                    "bio": current_user.bio,
                }
            }
        )
    except Exception as e:
        session.rollback()  # Rollback in case of any error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the profile"
        )

@router.get("/{user_id}")
def read_user_by_id(user_id: int, session: SessionDep):
    user = get_user_from_id(user_id, session)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": f"User with ID '{user_id}' found",
            "data": {
                "id": user.id,
                "username": user.username,
                "bio": user.bio
            }
        }
    )
