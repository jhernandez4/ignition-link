from typing import Annotated
from fastapi import Depends
from sqlmodel import Field, Session, SQLModel, create_engine
import os
from dotenv import load_dotenv
from pydantic import EmailStr

load_dotenv()

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    firebase_uid: str = Field(index=True, unique=True)
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)

MYSQL_URI = os.getenv("MYSQL_URI")
engine = create_engine(MYSQL_URI)

# Create the models for all models defined above
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Create a database session
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]