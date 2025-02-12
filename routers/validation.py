from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from ..database import SessionDep, User
from sqlmodel import select
from pydantic import BaseModel

router = APIRouter(
    tags=["validation"]
)

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
   
def check_username_exists(
    username_to_validate,
    session
):
    existing_user = session.exec(
        select(User).where(User.username == username_to_validate)
    ).first()

    return bool(existing_user) 