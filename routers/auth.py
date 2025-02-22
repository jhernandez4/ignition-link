from fastapi import ( 
    APIRouter, HTTPException, Depends, status
)
from fastapi.responses import JSONResponse
from firebase_admin import auth, exceptions
from typing import Annotated
from ..database import User
from sqlmodel import select, Session
from pydantic import BaseModel
import datetime
from .validation import check_username_exists
from ..dependencies import (
    verify_firebase_token, verify_firebase_session_cookie,
    load_admin_emails, get_session
)

router = APIRouter()

# Dependency injections
TokenDep = Annotated[dict, Depends(verify_firebase_token)]
CookieDep = Annotated[dict, Depends(verify_firebase_session_cookie)]
SessionDep = Annotated[Session, Depends(get_session)]

class SignUpRequest(BaseModel):
    username: str

@router.post("/signup")
def register_user(
    request: SignUpRequest,
    token: TokenDep, 
    session: SessionDep,
):
    # Check if the username is already taken
    username_taken = check_username_exists(request.username, session)

    if username_taken:
        raise HTTPException(status_code=400, detail="Username is already taken.")

    decoded_token = auth.verify_id_token(token)
    firebase_user = auth.get_user(uid=decoded_token['uid'])

    # Check if user with the same firebase_uid already exists
    existing_user = session.exec(
        select(User).where(User.firebase_uid == decoded_token['uid'])
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists.")

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
            key='session',
            value=session_cookie,
            expires=expires,
            httponly=True,
            secure=True,
            samesite="none"
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
        response.set_cookie('session', '', expires=0, httponly=True, secure=True, samesite="none")

        return response
    
    except auth.InvalidSessionCookieError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session cookie is invalid or expired. Please log in again."
        )