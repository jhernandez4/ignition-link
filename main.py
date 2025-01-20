from fastapi import FastAPI
from .database import User, create_db_and_tables, SessionDep
from .routers import auth

app = FastAPI()

app.include_router(auth.router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
async def root():
    return {"message": "Hello World"}
