from sqlmodel import (
    Field, Session, SQLModel, create_engine, select, Relationship
)
import os
import csv
from dotenv import load_dotenv
from pydantic import EmailStr
from datetime import datetime, timezone 
import requests
import io

load_dotenv()

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    firebase_uid: str = Field(index=True, unique=True)
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_admin: bool = Field(default=False)
    bio: str = Field(default="TESTING DEFAULT BIO")
    profile_pic_url: str = Field(default="https://i.imgur.com/L5AoglL.png")

    posts: list["Post"] = Relationship(back_populates="user")

class Post(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    post_image_url: str # Every post must have an image url 
    caption: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    edited_at: datetime | None = Field(default=None)

    # Every post must come from a user, so can't be none
    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="posts")

class Vehicles(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    make: str
    model: str
    year: int

PSQL_URI = os.getenv("PSQL_URI")

if not PSQL_URI:
    raise ValueError("PSQL_URI is not set in the environment variables")

engine = create_engine(PSQL_URI)

# Create the models for all models defined above
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def convert_csv_to_db(filename: str):
    with Session(engine) as session:
        # Check if the Vehicles table has any records
        existing_vehicle = session.exec(select(Vehicles)).first()
        if existing_vehicle:
            print("Database already populated. Skipping CSV import.")
            return  

    print("Database is empty. Populating from CSV...")

    if filename.startswith("http"):  # Check if it's a URL
        response = requests.get(filename)
        response.raise_for_status() 
        file_content = io.StringIO(response.text)

    else:
        file_content = open(filename, newline="", encoding="utf-8")  # Open local file

    with file_content as file:
        cars = csv.DictReader(file)
        with Session(engine) as session:
            try:
                for row in cars:
                    if len(row) < 3:  # Ensure row has all required fields
                        print(f"Skipping malformed row: {row}")
                        continue
                    
                    try:
                        vehicle = Vehicles(make=str(row['make']), model=str(row['model']), year=int(row['year']))
                        session.add(vehicle)
                        print(f"Adding vehicle to db: {vehicle}")
                    except ValueError as e:
                        print(f"Skipping Incorrect Row: {row}, Error: {e}")
                session.commit()
                print("Commit Successful!")
            except Exception as e:
                session.rollback()
                print(f"Error occurred: {e}")
            finally:
                session.close()