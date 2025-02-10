from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from ..database import SessionDep, User
from sqlmodel import select
router = APIRouter(
    tags=["validation"]
)

@router.post("/check-username")
def check_username(
    username: str,
    session: SessionDep
):
    if check_username_exists(username, session):
        HTTPException(status_code=400, detail="Username is already taken.")
    
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