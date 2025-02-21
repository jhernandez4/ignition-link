from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from ..database import User, engine
from sqlmodel import select, Session
from firebase_admin import auth, exceptions
from typing import Annotated

# Create a database session
def get_session():
    with Session(engine) as session:
        yield session

def check_username_exists(username_to_validate, session):
    existing_user = session.exec(
        select(User).where(User.username == username_to_validate)
    ).first()

    return bool(existing_user) 

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