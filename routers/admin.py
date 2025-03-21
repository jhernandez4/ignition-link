from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from firebase_admin import auth, exceptions
from typing import Annotated
from sqlmodel import select, Session
from ..database import Post, User
from ..models import UserResponse
from ..dependencies import (
    get_session, encode_model_to_json, get_current_user_is_admin
)

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUserAdminDep = Annotated[User, Depends(get_current_user_is_admin)]

@router.delete("/delete-post/{post_id}")
def delete_post_by_id(
    post_id: str,
    current_admin: CurrentUserAdminDep,
    session: SessionDep,
):
    post = session.exec(
        select(Post)
        .where(Post.id == post_id)
    ).first()

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No post found with id {post_id}"
        )

    session.delete(post)
    session.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": f"Successfully delete post with ID {post_id}",
        }
    )

@router.delete("/delete-user")
def delete_user_by_username(
    username: str,
    current_admin: CurrentUserAdminDep,
    session: SessionDep
):
    user_to_delete = session.exec(
        select(User)
        .where(User.username == username)
    ).first()

    if user_to_delete is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No user found with username {username}"
        )

    # Delete user from Firebase first
    auth.delete_user(user_to_delete.firebase_uid)

    session.delete(user_to_delete)
    session.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": f"User with username '{username}' has been deleted"
        }
    )

@router.patch("/deactivate-user")
def deactivate_user_by_username(
    username: str,
    current_admin: CurrentUserAdminDep,
    session: SessionDep
):
    user_to_deactivate = session.exec(
        select(User)
        .where(User.username == username)
    ).first()

    if user_to_deactivate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username {username} not found"
        )

    auth.update_user(
        uid = user_to_deactivate.firebase_uid,
        disabled = True
    )    

    # Invalidate user's existing session cookie 
    auth.revoke_refresh_tokens(uid = user_to_deactivate.firebase_uid)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": f"Successfully deactivated user with username '{username}'"
        }
    )

@router.patch("/activate-user")
def activate_user_by_username(
    username: str,
    current_admin: CurrentUserAdminDep,
    session: SessionDep
):
    user_to_activate = session.exec(
        select(User)
        .where(User.username == username)
    ).first()

    if user_to_activate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username '{username}' not found"
        )

    auth.update_user(
        uid = user_to_activate.firebase_uid,
        disabled = False
    )    

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": f"Successfully reactivated user with username '{username}'"
        }
    )

@router.get("/get-users")
def get_all_users(
    current_admin: CurrentUserAdminDep,
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100
):
    users_list = session.exec(
        select(User)
        .offset(offset)
        .limit(limit)
    ).all()

    if users_list is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users found"
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": f"Successfully retrieved users",
            "content": [
                UserResponse.model_validate(user).model_dump()
                for user in users_list
            ]
        }
    )
