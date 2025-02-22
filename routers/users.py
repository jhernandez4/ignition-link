from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from ..dependencies import (
    get_session, verify_firebase_session_cookie, get_user_from_uid
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
async def read_user_me(request: UIDRequest, session: SessionDep):
    user = get_user_from_uid(request.uid, session)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "User found",
            "data": {
                "username": user.username,
            }
        }
    )
    
