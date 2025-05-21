from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import (
    create_db_and_tables, convert_csv_to_db, populate_part_types,
    insert_brands_to_db, import_unique_vehicles_from_csv, install_fuzzy_search_extension
)
from .routers import (
    auth, comments, likes, validation, users, posts, admin, vehicles, builds, parts, scrape, follow
)
import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv
import os
# import csv
# import sys

# # csv.field_size_limit(sys.maxsize)

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
app.include_router(vehicles.router)
app.include_router(builds.router)
app.include_router(parts.router)
app.include_router(scrape.router)
app.include_router(follow.router)
app.include_router(comments.router)
app.include_router(likes.router)

@app.on_event("startup")
def on_startup():
    VEHICLES_CSV_PATH = os.getenv("VEHICLES_CSV_PATH")
    if not VEHICLES_CSV_PATH:
        raise RuntimeError("VEHICLES_CSV_PATH is not set in the environment variables.")

    BRANDS_TXT_PATH = os.getenv("BRANDS_TXT_PATH")
    if not BRANDS_TXT_PATH:
        raise RuntimeError("BRANDS_TXT_PATH is not set in the environment variables")

    UNIQUE_VEHICLES_CSV_PATH = os.getenv("UNIQUE_VEHICLES_CSV_PATH")
    if not UNIQUE_VEHICLES_CSV_PATH:
        raise RuntimeError("UNIQUE_VEHICLES_CSV_PATH is not set in the environment variables.")

    create_db_and_tables()
    convert_csv_to_db(VEHICLES_CSV_PATH)
    insert_brands_to_db(BRANDS_TXT_PATH)
    populate_part_types()
    import_unique_vehicles_from_csv(UNIQUE_VEHICLES_CSV_PATH)
    install_fuzzy_search_extension()

    # Initialize Firebase
    firebase_key_path = os.getenv("FIREBASE_KEY_PATH")
    if not firebase_key_path:
        raise RuntimeError("FIREBASE_KEY_PATH is not set in the environment variables.")
    
    cred = credentials.Certificate(firebase_key_path)
    firebase_admin.initialize_app(cred)

@app.get("/")
async def root():
    return {"message": "Hello World"}
