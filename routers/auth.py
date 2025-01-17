from fastapi import APIRouter, Request, HTTPException
import firebase_admin
from firebase_admin import credentials, auth
from dotenv import load_dotenv
import os
from database import User, create_db_and_tables, SessionDep

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