from sqlmodel import Field, Session, SQLModel, Relationship, create_engine, select
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

    builds: list["Builds"] = Relationship(back_populates="owner")

class Vehicles(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    make: str
    model: str
    year: int

class Builds(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    garage: str
    car: str
    exhaust: Optional[str] = None
    wheels: Optional[str] = None
    suspension: Optional[str] = None
    intake: Optional[str] = None
    forced_injection: Optional[str] = None
    interior_cosmetics: Optional[str] = None
    exterior_cosmetics: Optional[str] = None
    fueling: Optional[str] = None
    brakes: Optional[str] = None
    tune: Optional[str] = None
    body: Optional[str] = None

    owner: User = Relationship(back_populates="builds")

class Part(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    car: str
    type: str
    brand: str
    model: str

# Create many-to-many relationship between Parts and Builds tables
class ConnectBuildsParts(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    build_id: int = Field(foreign_key="builds.id", primary_key=None)
    part_id: int = Field(foreign_key="part.id", primary_key=None)

PSQL_URI = os.getenv("PSQL_URI")

if not PSQL_URI:
    raise ValueError("PSQL_URI is not set in the environment variables")

engine = create_engine(PSQL_URI)

# Create the models for all models defined above
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def convert_parts_to_db(filename: str):
    with Session(engine) as session:
        # Check if the Parts table has any records
        existing_parts = session.exec(select(Part)).first()
        if existing_parts:
            print("Parts database already populated. Skipping CSV import.")
            return  

    print("Parts database is empty. Populating from CSV...")

    with open(filename, newline="", encoding="utf-8") as file:
        parts = csv.DictReader(file)
        with Session(engine) as session:
            try:
                for row in parts:
                    if len(row) < 4:  # Ensure row has all required fields
                        print(f"Skipping malformed row: {row}")
                        continue
                    
                    try:
                        parts = Part(car=str(row['car']), type=str(row['type']), brand=str(row['brand']), model=str(row['model']))
                        session.add(parts)
                    except ValueError as e:
                        print(f"Skipping Incorrect Row: {row}, Error: {e}")
                session.commit()
                print("Commit Successful!")
            except Exception as e:
                session.rollback()
                print(f"Error occurred: {e}")
            finally:
                session.close()

def convert_csv_to_db(filename: str):
    with Session(engine) as session:
        # Check if the Vehicles table has any records
        existing_vehicle = session.exec(select(Vehicles)).first()
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

def add_part_to_build(build_id: int, part_id: int):
    with Session(engine) as session:
        parts = session.exec(select(Part)).all()

    if not parts:
        return "No Parts Found"
    
    print ("Available Parts: ")
    for part in parts:
        print(f"{part.id}) {part.type}: {part.brand} {part.model}")

    # Check if build and part exist
    build = session.exec(select(Builds).where(Builds.id == build_id)).first()
    part = session.exec(select(Part).where(Part.id == part_id)).first()

    if not build or not part:
        return "No Build or Part found!"
    
    existing_link = session.exec(select(ConnectBuildsParts).where(ConnectBuildsParts.build_id == build_id, ConnectBuildsParts.part_id == part_id))

    if existing_link:
        return "Part is already added to the Build"
    
    link = ConnectBuildsParts(build_id=build_id, part_id=part_id)
    session.add(link)
    session.commit()

    return f"Added {part.brand} {part.model} to Build {build.id}"

def get_db():
    with Session(engine) as session:
        yield session
