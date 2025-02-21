from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from typing import Annotated
from sqlmodel import Session
from pydantic import BaseModel
from .dependencies import check_username_exists, get_session

router = APIRouter(
    tags=["validation"]
)

# Dependency injection
SessionDep = Annotated[Session, Depends(get_session)]

class UsernameCheckRequest(BaseModel):
    username: str

@router.post("/check-username")
def check_username(
    request: UsernameCheckRequest,
    session: SessionDep
):
    if check_username_exists(request.username, session):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken.")
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Username is available"
        }
    ) 
   