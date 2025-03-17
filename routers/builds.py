from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import Annotated
from sqlmodel import select, Session
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from datetime import datetime, timezone 
from ..database import Post, User, Vehicle, Build
from ..models import BuildResponse 
from ..dependencies import (
    get_session, get_user_from_cookie, encode_model_to_json
)

router = APIRouter(
    prefix="/builds",
    tags=["builds"],
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUserDep = Annotated[User, Depends(get_user_from_cookie)]

class CreateBuildRequest(BaseModel):
    vehicle_id: int

@router.post("/", response_model=BuildResponse)
def create_build(
    request: CreateBuildRequest,
    current_user: CurrentUserDep,
    session: SessionDep
):
    new_build = Build(
        user_id=current_user.id,
        vehicle_id=request.vehicle_id
    )

    session.add(new_build)
    session.commit()
    session.refresh(new_build)

    return new_build 