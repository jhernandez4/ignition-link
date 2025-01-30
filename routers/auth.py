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

def load_admin_emails():
    try:
        with open('admin_emails.txt', 'r') as file:
            emails = file.read().splitlines()  # Read each line into a list
            return emails
    except FileNotFoundError:
        return []  
    except Exception as e:
        return []  

TokenDep = Annotated[dict, Depends(verify_firebase_token)]

@router.post("/signup")
def register_user(
    id_token: TokenDep, 
    session: SessionDep,
):
    firebase_user = auth.get_user(uid=id_token['uid'])

    # Check if user with the same firebase_uid already exists
    existing_user = session.exec(
        select(User).where(User.firebase_uid == id_token['uid'])
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists.")

    # Check if the username is already taken
    username_taken = session.exec(
        select(User).where(User.username == firebase_user.display_name)
    ).first()

    if username_taken:
        raise HTTPException(status_code=400, detail="Username is already taken.")

    # Set admin role 
    admin_emails = load_admin_emails()
    is_admin = firebase_user.email in admin_emails


    # Create new user
    new_user = User(
        firebase_uid=id_token['uid'],
        username=firebase_user.display_name,
        email=firebase_user.email,
        is_admin=is_admin
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