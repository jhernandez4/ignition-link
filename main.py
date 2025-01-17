from fastapi import FastAPI
from database import User, create_db_and_tables, SessionDep

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
async def root():
    return {"message": "Hello World"}
