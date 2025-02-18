from typing import Annotated
from fastapi import Depends
from sqlmodel import Field, Session, SQLModel, create_engine
import os
import csv
from dotenv import load_dotenv
from pydantic import EmailStr
from datetime import datetime, timezone 

load_dotenv()

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    firebase_uid: str = Field(index=True, unique=True)
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_admin: bool = Field(default=False)

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

# Create a database session
def get_session():
    with Session(engine) as session:
        yield session

def convert_csv_to_db(filename: str):
    with open(filename, newline="", encoding="utf-8") as file:
        cars = csv.reader(file)
        next(cars, None)
        with Session(engine) as session:
            for row in cars:
                if len(row) < 3:  # Ensure row has all required fields
                    print(f"Skipping malformed row: {row}")
                    continue
                
                try:
                    vehicle = Vehicles(make=row[0], model=row[1], year=int(row[2]))
                    session.add(vehicle)
                except ValueError:
                    print(f"Skipping Incorrect Row: {row}")
            session.commit()
    print("Successfully Converted")

SessionDep = Annotated[Session, Depends(get_session)]