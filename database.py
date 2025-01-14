from typing import Annotated
from sqlmodel import Field, Session, SQLModel, create_engine, select
import os
from dotenv import load_dotenv

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)