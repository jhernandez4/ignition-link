from sqlmodel import (
    Field, Session, SQLModel, create_engine, select, Relationship
)
import os
import csv
from dotenv import load_dotenv
from pydantic import EmailStr
from datetime import datetime, timezone 
from typing import Optional
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

    builds: list["Build"] = Relationship(back_populates="owner")

class Vehicle(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    make: str
    model: str
    year: int
    
    builds: list["Build"] = Relationship(back_populates="vehicle")


class Build(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    vehicle_id: int = Field(foreign_key="vehicles.id")
    nickname: str | None = Field(default=None)
    cover_picture_url: str | None = Field(
        default="https://cdn2.iconfinder.com/data/icons/solidix-cars/128/cars_vehicle_motor_front-14-512.png"
    )
    description: str | None = Field(default="")
    

    owner: User = Relationship(back_populates="builds")
    vehicle: Vehicle = Relationship(back_populates="builds")
    parts: list["Part"] = Relationship(back_populates="builds", link_model="BuildPartLink")

class Part(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    type: str
    brand: str
    part_name: str

    builds: list["Build"] = Relationship(back_populates="parts", link_model="BuildPartLink")


# Create many-to-many relationship between Parts and Builds tables
class BuildPartLink(SQLModel, table=True):
    build_id: int = Field(default=None, foreign_key="build.id", primary_key=True)
    part_id: int = Field(default=None, foreign_key="part.id", primary_key=True)

    # exhaust: Optional[str] = None
    # wheels: Optional[str] = None
    # suspension: Optional[str] = None
    # intake: Optional[str] = None
    # forced_injection: Optional[str] = None
    # interior_cosmetics: Optional[str] = None
    # exterior_cosmetics: Optional[str] = None
    # fueling: Optional[str] = None
    # brakes: Optional[str] = None
    # tune: Optional[str] = None
    # body: Optional[str] = None

PSQL_URI = os.getenv("PSQL_URI")

if not PSQL_URI:
    raise ValueError("PSQL_URI is not set in the environment variables")

engine = create_engine(PSQL_URI)

# Create the models for all models defined above
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# def convert_parts_to_db(filename: str):
#     with Session(engine) as session:
#         # Check if the Parts table has any records
#         existing_parts = session.exec(select(Part)).first()
#         if existing_parts:
#             print("Parts database already populated. Skipping CSV import.")
#             return  

#     print("Parts database is empty. Populating from CSV...")

#     with open(filename, newline="", encoding="utf-8") as file:
#         parts = csv.DictReader(file)
#         with Session(engine) as session:
#             try:
#                 for row in parts:
#                     if len(row) < 4:  # Ensure row has all required fields
#                         print(f"Skipping malformed row: {row}")
#                         continue
                    
#                     try:
#                         parts = Part(car=str(row['car']), type=str(row['type']), brand=str(row['brand']), model=str(row['model']))
#                         session.add(parts)
#                     except ValueError as e:
#                         print(f"Skipping Incorrect Row: {row}, Error: {e}")
#                 session.commit()
#                 print("Commit Successful!")
#             except Exception as e:
#                 session.rollback()
#                 print(f"Error occurred: {e}")
#             finally:
#                 session.close()

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
            try:
                for row in cars:
                    if len(row) < 3:  # Ensure row has all required fields
                        print(f"Skipping malformed row: {row}")
                        continue
                    
                    try:
                        vehicle = Vehicle(make=str(row['make']), model=str(row['model']), year=int(row['year']))
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

# def add_part_to_build(build_id: int, part_id: int):
#     with Session(engine) as session:
#         parts = session.exec(select(Part)).all()

#     if not parts:
#         return "No Parts Found"
    
#     print ("Available Parts: ")
#     for part in parts:
#         print(f"{part.id}) {part.type}: {part.brand} {part.model}")

#     # Check if build and part exist
#     build = session.exec(select(Build).where(Build.id == build_id)).first()
#     part = session.exec(select(Part).where(Part.id == part_id)).first()

#     if not build or not part:
#         return "No Build or Part found!"
    
#     existing_link = session.exec(select(BuildPartLink).where(BuildPartLink.build_id == build_id, BuildPartLink.part_id == part_id))

#     if existing_link:
#         return "Part is already added to the Build"
    
#     link = BuildPartLink(build_id=build_id, part_id=part_id)
#     session.add(link)
#     session.commit()

#     return f"Added {part.brand} {part.model} to Build {build.id}"

def get_db():
    with Session(engine) as session:
        yield session
