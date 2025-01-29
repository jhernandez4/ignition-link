from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from firebase_admin import auth
from typing import Annotated
from ..database import SessionDep, User
from sqlmodel import SQLModel, select
from pydantic import EmailStr

router = APIRouter()

# OAuth2PasswordBearer will fetch the token from the "Authorization" header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def verify_firebase_token(token: str = Depends(oauth2_scheme)):
    try:
        # Decode and verify the token using Firebase Admin SDK
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token['uid']
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is invalid or expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return decoded_token 

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
        )

TokenDep = Annotated[dict, Depends(verify_firebase_token)]

class UserCreate(SQLModel):
    username: str 
    email: EmailStr 

@router.post("/signup")
def register_user(
    token: TokenDep, 
    session: SessionDep,
    user_request: UserCreate
):
    # Check if user with the same firebase_uid already exists
    existing_user = session.exec(
        select(User).where(User.firebase_uid == token['uid'])
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists.")

    # Check if the username is already taken
    username_taken = session.exec(
        select(User).where(User.username == user_request.username)
    ).first()

    if username_taken:
        raise HTTPException(status_code=400, detail="Username is already taken.")

    # Create new user
    new_user = User(
        firebase_uid=token['uid'],
        username=user_request.username,
        email=user_request.email,
    )

    try:
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return JSONResponse(
        status_code=201,  
        content={
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email
        }
    )