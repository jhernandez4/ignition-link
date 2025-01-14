from typing import Annotated
from fastapi import Depends
from sqlmodel import Field, Session, SQLModel, create_engine
import os
from dotenv import load_dotenv

load_dotenv()

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)

MYSQL_URI = os.getenv("MYSQL_URI")
connect_args = {"check_same_thread": False}
engine = create_engine(MYSQL_URI, connect_args=connect_args)

# Create the models for all models defined above
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Create a database session
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]