from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import firebase_admin
from firebase_admin import credentials, auth
from dotenv import load_dotenv
import os
from typing import Annotated
from ..database import SessionDep, User
from sqlmodel import SQLModel, select
from pydantic import EmailStr

router = APIRouter()

load_dotenv()

FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH")
cred = credentials.Certificate(FIREBASE_KEY_PATH)
firebase_admin.initialize_app(cred)

async def verify_token(request: Request):
    try:
        # Extract Firebase ID token from the Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid token")
        
        id_token = auth_header.split(" ")[1]

        # Verify the token using Firebase Admin SDK
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token.get("uid")

        return {"status": "success", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

TokenDep = Annotated[dict, Depends(verify_token)]

class UserCreate(SQLModel):
    firebase_uid: str 
    username: str 
    email: EmailStr 

@router.post("/signup")
def register_user(
    token: TokenDep, 
    session: SessionDep,
    user_request: UserCreate
):
    # Check if user already exists
    existing_user = session.exec(
        select(User).where(User.firebase_uid == user_request.firebase_uid)
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists.")

    # Create new user
    new_user = User(
        firebase_uid=user_request.firebase_uid,
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