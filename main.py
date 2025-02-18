from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import User, create_db_and_tables, SessionDep
from .routers import auth, validation
import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv
import os

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:5173",
    "https://ignitionlink-frontend.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth.router)
app.include_router(validation.router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

    # Initialize Firebase
    firebase_key_path = os.getenv("FIREBASE_KEY_PATH")
    if not firebase_key_path:
        raise RuntimeError("FIREBASE_KEY_PATH is not set in the environment variables.")
    
    cred = credentials.Certificate(firebase_key_path)
    firebase_admin.initialize_app(cred)

@app.get("/")
async def root():
    return {"message": "Hello World"}
