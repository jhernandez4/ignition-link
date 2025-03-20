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

@router.post("", response_model=BuildResponse)
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

@router.get("/{build_id}", response_model=BuildResponse)
def get_build_from_build_id(
    build_id: int,
    session: SessionDep
):
    build = session.exec(
        select(Build)
        .where(Build.id == build_id)
    ).first()

    if not build: 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to retrieve build. Build with id {build_id} does not exist."
        )

    return build

@router.get("", response_model=list[BuildResponse])
def get_builds_from_user_id(
    user_id: int,
    session: SessionDep,
    offset: int = 0,
    # Less than or equal to 100; default to 100
    limit: Annotated[int, Query(le=100)] = 100,
):
    builds_from_user_id = session.exec(
        select(Build)
        .where(Build.user_id == user_id)
        .order_by(Build.id.asc())
        .offset(offset)
        .limit(limit)
    ).all()
    
    if builds_from_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to retrieve builds. List of builds is null"
        )
    
    return builds_from_user_id