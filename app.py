from fastapi import FastAPI
import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv
import os

load_dotenv

FIREBASE_KEY_PATH = os.environ.get("FIREBASE_KEY_PATH")
cred = credentials.Certificate(FIREBASE_KEY_PATH)
firebase_admin.initialize_app(cred)

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}