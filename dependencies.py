from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from fastapi.encoders import jsonable_encoder
from .database import User, engine
from sqlmodel import select, Session
from sqlalchemy.exc import SQLAlchemyError
from firebase_admin import auth, exceptions
from typing import Annotated
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv
import os

# Create a database session
def get_session():
    with Session(engine) as session:
        yield session

def check_username_exists(username_to_validate, session):
    existing_user = session.exec(
        select(User).where(User.username == username_to_validate)
    ).first()

    return bool(existing_user) 

# Used to return Pydantic model in JSONResponse
def encode_model_to_json(model: BaseModel):
    return jsonable_encoder(model.model_dump())

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

        return token 

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
        )

# Dependency for verifying the session cookie
async def verify_firebase_session_cookie(session: Annotated[str | None, Cookie()] = None):
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session cookie is missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Decode and verify the session cookie using Firebase Admin SDK
        decoded_claims = auth.verify_session_cookie(session, check_revoked=True)
        user_id = decoded_claims['uid']

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session cookie is invalid or expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return decoded_claims

    except exceptions.FirebaseError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Session cookie verification failed: {str(e)}",
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

def get_user_from_uid(firebase_uid, session):
    try:
        user = session.exec(
            select(User).where(User.firebase_uid == firebase_uid)
        ).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with UID {firebase_uid} does not exist"
            )

        return user
    except SQLAlchemyError as e:
        # Log the error here if needed
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while querying the database."
        ) from e

def get_user_from_cookie(
    decoded_claims: Annotated[dict, Depends(verify_firebase_session_cookie)],
    session: Annotated[Session, Depends(get_session)]
):
    current_user_uid = decoded_claims['uid']
    
    try:
        user = get_user_from_uid(current_user_uid, session)
    except HTTPException as e:
        raise e  # Forward the original exception
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving user"
        ) from e

    return user

def get_current_user_is_admin(
    current_user: Annotated[User, Depends(get_user_from_cookie)]
):
    if current_user.is_admin:
        return current_user 
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access denied: Admin privileges required"
        )

def get_gemini_client():
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_APIKEY is not set in environment variables")

    client = genai.Client(api_key=GEMINI_API_KEY)

    return client
