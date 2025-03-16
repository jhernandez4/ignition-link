from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import create_db_and_tables, convert_csv_to_db
from .routers import auth, validation, users, posts, admin
import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv
import os

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:5173",
    "https://ignitionlink-frontend.vercel.app",
    "https://ignition-link-backup.netlify.app",
    "https://ignitionlink.netlify.app"
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
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(admin.router)

@app.on_event("startup")
def on_startup():
    VEHICLES_CSV_PATH = os.getenv("VEHICLES_CSV_PATH")
    if not VEHICLES_CSV_PATH:
        raise RuntimeError("VEHICLES_CSV_PATH is not set in the environment variables.")

    create_db_and_tables()
    convert_csv_to_db(VEHICLES_CSV_PATH)
    # convert_parts_to_db("parts.csv")
    # add_part_to_build()

    # Initialize Firebase
    firebase_key_path = os.getenv("FIREBASE_KEY_PATH")
    if not firebase_key_path:
        raise RuntimeError("FIREBASE_KEY_PATH is not set in the environment variables.")
    
    cred = credentials.Certificate(firebase_key_path)
    firebase_admin.initialize_app(cred)

@app.get("/")
async def root():
    return {"message": "Hello World"}
