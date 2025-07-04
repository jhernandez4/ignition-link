from sqlmodel import (
    Field, Session, SQLModel, create_engine, select, Relationship,
    UniqueConstraint
)
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
import os
import csv
from dotenv import load_dotenv
from pydantic import EmailStr
from datetime import datetime, timezone 
from typing import Optional
import requests
import io
import re

load_dotenv()

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    firebase_uid: str = Field(index=True, unique=True)
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_admin: bool = Field(default=False)
    bio: str = Field(default="")
    profile_pic_url: str = Field(default="https://i.imgur.com/L5AoglL.png")

    posts: list["Post"] = Relationship(back_populates="user")
    comments: list["Comment"] = Relationship(back_populates="user")
    likes: list["Like"] = Relationship(back_populates="user")
    builds: list["Build"] = Relationship(back_populates="owner")
    part_submissions: list["Part"] = Relationship(back_populates="submitted_by")
    following: list["Follow"] = Relationship(back_populates="follower", sa_relationship_kwargs={"foreign_keys": "[Follow.follower_id]"})
    followers: list["Follow"] = Relationship(back_populates="following", sa_relationship_kwargs={"foreign_keys": "[Follow.following_id]"})

class Post(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    post_image_url: str # Every post must have an image url 
    caption: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    edited_at: datetime | None = Field(default=None)

    # Every post must come from a user, so can't be none
    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="posts")

    # Display Likes and Comments
    comments: list["Comment"] = Relationship(back_populates="post")
    likes: list["Like"] = Relationship(back_populates="post")

class Like(SQLModel, table=True):
    post_id: int = Field(default=None, foreign_key="post.id", primary_key=True)
    user_id: int = Field(default=None, foreign_key="user.id", primary_key=True)
    liked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: User = Relationship(back_populates="likes")
    post: Post = Relationship(back_populates="likes")

class Comment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="post.id")
    user_id: int = Field(foreign_key="user.id")
    comment: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: User = Relationship(back_populates="comments")
    post: Post = Relationship(back_populates="comments")

class Vehicle(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    make: str = Field(default=None, index=True)
    model: str = Field(default=None, index=True)
    year: int = Field(default=None, index=True)

    builds: list["Build"] = Relationship(back_populates="vehicle")

    __table_args__ = (
        UniqueConstraint('year', 'make', 'model', name='uix_year_make_model'),
    )

class Follow(SQLModel, table=True):
    follower_id: int = Field(foreign_key="user.id", primary_key=True)
    following_id: int = Field(foreign_key="user.id", primary_key=True)
    followed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    follower: User = Relationship(back_populates="following", sa_relationship_kwargs={"foreign_keys": "[Follow.follower_id]"})
    following: User = Relationship(back_populates="followers", sa_relationship_kwargs={"foreign_keys": "[Follow.following_id]"})

# Create many-to-many relationship between Parts and Builds tables
class BuildPartLink(SQLModel, table=True):
    build_id: int = Field(default=None, foreign_key="build.id", primary_key=True)
    part_id: int = Field(default=None, foreign_key="part.id", primary_key=True)

class Build(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    vehicle_id: int = Field(foreign_key="vehicle.id")
    nickname: str | None = Field(default=None)
    cover_picture_url: str | None = Field(default="https://i.imgur.com/wfqeko6.png")
    description: str | None = Field(default=None)
    
    owner: User = Relationship(back_populates="builds")
    vehicle: Vehicle = Relationship(back_populates="builds")
    parts: list["Part"] = Relationship(back_populates="builds", link_model=BuildPartLink)

class PartType(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    type: str 
    slug: str = Field(index=True)

    parts: list["Part"] = Relationship(back_populates="part_type")

class Brand(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    slug: str = Field(index=True, unique=True)

    parts: list["Part"] = Relationship(back_populates="brand")

class Part(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    brand_id: int = Field(foreign_key="brand.id")
    submitted_by_id: int = Field(foreign_key="user.id")
    type_id: int = Field(foreign_key="parttype.id")
    part_name: str = Field(index=True)
    part_number: str | None = Field(default=None)
    image_url: str | None = Field(default=None)
    description: str | None = Field(default=None)
    is_verified: bool = Field(default=False) # for admin/mods to finalize image, brand, number, etc
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    brand: Brand = Relationship(back_populates="parts")
    builds: list["Build"] = Relationship(back_populates="parts", link_model=BuildPartLink)
    part_type: PartType = Relationship(back_populates="parts")
    submitted_by: User = Relationship(back_populates="part_submissions")

PSQL_URI = os.getenv("PSQL_URI")

if not PSQL_URI:
    raise ValueError("PSQL_URI is not set in the environment variables")

engine = create_engine(PSQL_URI)

# Create the models for all models defined above
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

def insert_brands_to_db(filename: str):
    with Session(engine) as session:
        existing_brand = session.exec(select(Brand)).first()
        if existing_brand:
            print("Brand table already populated. Skipping brand insertions")
            return

    print("Brand table is empty. Populating from CSV...")
    if filename.startswith("http"):
        response = requests.get(filename)
        response.raise_for_status() 
        file_content = io.StringIO(response.text)
    else:
        file_content = open(filename, newline="r", encoding="utf-8")  # Open local file

    with file_content as file:
        brands_list = [line.strip() for line in file if line.strip()]
    
    with Session(engine) as session:
        for new_brand in brands_list:
            slug = slugify(new_brand)
            new_brand = Brand(name=new_brand, slug=slug)
            session.add(new_brand)
            session.commit()
            session.refresh(new_brand)
            print(f"{new_brand.name} added to the brand table")

def convert_csv_to_db(filename: str):
    with Session(engine) as session:
        # Check if the Vehicles table has any records
        existing_vehicle = session.exec(select(Vehicle)).first()
        if existing_vehicle:
            print("Vehicles database already populated. Skipping CSV import.")
            return  

    print("Vehicles database is empty. Populating from CSV...")

    if filename.startswith("http"):  # Check if it's a URL
        response = requests.get(filename)
        response.raise_for_status() 
        file_content = io.StringIO(response.text)

    else:
        file_content = open(filename, newline="", encoding="utf-8")  # Open local file

    with file_content as file:
        cars = csv.DictReader(file)
        with Session(engine) as session:
            for row in cars:
                if len(row) < 3:  # Ensure row has all required fields
                    print(f"Skipping malformed row: {row}")
                    continue
                
                try:
                    # Create the Vehicle object
                    vehicle = Vehicle(make=str(row['make']), model=str(row['model']), year=int(row['year']))
                    session.add(vehicle)
                    print(f"Adding vehicle to db: {vehicle}")

                    # Try to commit the individual vehicle, handle integrity violation
                    try:
                        session.commit()
                        print(f"Vehicle committed: {vehicle}")
                    except IntegrityError as e:
                        session.rollback()  # Rollback only for this specific row
                        print(f"IntegrityError occurred for {vehicle}: {e.orig} - Skipping this row.")
                except ValueError as e:
                    print(f"Skipping Incorrect Row: {row}, Error: {e}")

            print("CSV import complete.")

def populate_part_types():
    types = [
        "Brakes",
        "Engine",
        "Exhaust",
        "Exterior",
        "Forced Induction",
        "Fueling",
        "Intake",
        "Interior",
        "Suspension",
        "Tune",
        "Wheels",
        "Other"
    ]

    with Session(engine) as session:
        part_types_db = session.exec(
            select(PartType)
        ).all()

        if part_types_db:
            print("Part types table populated. Skipping import")
            return
        else:
            for type_name in types:
                slug = slugify(type_name)
                new_type = PartType(type=type_name, slug=slug)
                session.add(new_type)
            session.commit() 
            print("Part types imported to tables.")

def import_unique_vehicles_from_csv(filename: str):
    with Session(engine) as session:
        # Check if the Vehicles table has any records
        existing_vehicle = session.exec(select(Vehicle)).first()
        if existing_vehicle:
            print("Vehicles database already populated. Skipping CSV import.")
            return  

    print("Vehicles database is empty. Populating from CSV...")

    if filename.startswith("http"):  # Check if it's a URL
        response = requests.get(filename)
        response.raise_for_status() 
        file_content = io.StringIO(response.text)

    else:
        file_content = open(filename, newline="", encoding="utf-8")  # Open local file

    with file_content as file:
        cars = csv.DictReader(file)
        cars_count = 0
        with Session(engine) as session:
            for row in cars:
                if len(row) < 3:  # Ensure row has all required fields
                    print(f"Skipping malformed row: {row}")
                    continue
                
                try:
                    # Create the Vehicle object
                    vehicle = Vehicle(make=str(row['make']), model=str(row['model']), year=int(row['year']))
                    session.add(vehicle)
                    cars_count += 1
                    print(f"Adding vehicle to db: {vehicle}")

                except ValueError as e:
                    print(f"Skipping Incorrect Row: {row}, Error: {e}")

            try:
                session.commit()
                print(f"{cars_count} vehicles committed: {vehicle}")
            except IntegrityError as e:
                session.rollback()  # Rollback only for this specific row
                print(f"IntegrityError occurred for {vehicle}: {e.orig} - Skipping this row.")

            print("CSV import complete.")

    with Session(engine) as session:
        db_types = session.exec(select(PartType)).all()

        if not db_types:
            for type in db_types:
                new_type = PartType(type=type) 
                session.add(new_type)
                session.commit()
                session.refresh(new_type)
                print(f"Part type {new_type} has been added")
        else:
            print("Part types table is already populated. Skipping type insertions")

def get_db():
    with Session(engine) as session:
        yield session

def install_fuzzy_search_extension():
    with Session(engine) as session:
        print("Verifying installation for PSQL fuzzy search extension...")
        try:
            session.exec(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            session.commit()  # Commit the transaction if needed
            print("Extension pg_trgm installed successfully.")
        except Exception as e:
            print(f"Error installing extension: {e}")