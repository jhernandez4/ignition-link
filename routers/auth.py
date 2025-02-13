from fastapi import ( 
    APIRouter, HTTPException, Depends, status, Cookie, Form,
)
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from firebase_admin import auth, exceptions
from typing import Annotated
from ..database import SessionDep, User
from sqlmodel import SQLModel, select
from pydantic import EmailStr, BaseModel
import datetime
from .validation import check_username_exists

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

        return token 

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
        )

# Dependency for verifying the session cookie
async def verify_firebase_session_cookie(session_cookie: str = Cookie(None)):
    if not session_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session cookie is missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Decode and verify the session cookie using Firebase Admin SDK
        decoded_claims = auth.verify_session_cookie(session_cookie, check_revoked=True)
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

TokenDep = Annotated[dict, Depends(verify_firebase_token)]
CookieDep = Annotated[dict, Depends(verify_firebase_session_cookie)]

class SignUpRequest(BaseModel):
    username: str

@router.post("/signup")
def register_user(
    request: SignUpRequest,
    token: TokenDep, 
    session: SessionDep,
):
    decoded_token = auth.verify_id_token(token)
    firebase_user = auth.get_user(uid=decoded_token['uid'])

    # Check if user with the same firebase_uid already exists
    existing_user = session.exec(
        select(User).where(User.firebase_uid == decoded_token['uid'])
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists.")

    # Check if the username is already taken
    username_taken = check_username_exists(request.username, session)

    if username_taken:
        raise HTTPException(status_code=400, detail="Username is already taken.")

    # Set admin role 
    admin_emails = load_admin_emails()
    is_admin = firebase_user.email in admin_emails


    # Create new user
    new_user = User(
        firebase_uid=decoded_token['uid'],
        username=request.username,
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

@router.post("/session-login")
async def session_login(
    token: TokenDep
):
    # Set session expiration to 5 days.
    expires_in = datetime.timedelta(days=5)

    try:
        # Create the session cookie. This will also verify the ID token in the process.
        # The session cookie will have the same claims as the ID token.
        session_cookie = auth.create_session_cookie(token, expires_in=expires_in)
        response = JSONResponse({'status': 'success'})

        # Set cookie policy for session cookie.
        expires = datetime.datetime.now(datetime.UTC) + expires_in

        # Set the session cookie in the response
        response.set_cookie(
            'session',
            session_cookie,
            expires=expires,
            httponly=True,
            secure=True,
            samesite="strict"
        )

        return response
    except exceptions.FirebaseError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to create a session cookie")

@router.post("/logout")
def session_logout(
    decoded_claims: CookieDep
):
    try:
        auth.revoke_refresh_tokens(decoded_claims['sub'])
        response = JSONResponse({"status": "success"})
        # Clear the session cookie by setting expires to 0 (cookie will be deleted)
        response.set_cookie('session', '', expires=0, httponly=True, secure=True)

        return response
    
    except auth.InvalidSessionCookieError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session cookie is invalid or expired. Please log in again."
        )