from fastapi import FastAPI
import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv
import os

from database import User, create_db_and_tables, SessionDep

load_dotenv()

FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH")
cred = credentials.Certificate(FIREBASE_KEY_PATH)
firebase_admin.initialize_app(cred)

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
async def root():
    return {"message": "Hello World"}
