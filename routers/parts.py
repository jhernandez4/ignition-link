from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import Annotated
from sqlmodel import select, Session
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from datetime import datetime, timezone 
from ..database import User, PartType, Part, Brand
from ..models import PartResponse 
from ..dependencies import (
    get_session, get_user_from_cookie, encode_model_to_json
)

router = APIRouter(
    prefix="/parts",
    tags=["parts"],
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUserDep = Annotated[User, Depends(get_user_from_cookie)]

@router.get("/types", response_model=list[PartType])
def get_part_types(session: SessionDep):
    part_types_list = session.exec(
        select(PartType)
    ).all()

    if part_types_list is None: 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to retrieve part types. List is null"
        ) 

    return part_types_list

@router.get("/brands", response_model=list[Brand])
def get_brands_list(session: SessionDep):
    brands_list = session.exec(
        select(Brand)
        .order_by(Brand.name.asc())
    ).all()

    return brands_list

@router.get("/brands/query", response_model=list[Brand])
def query_brands(
    brand_name: str,
    session: SessionDep,
    offset: int = 0,
    # Less than or equal to 5; default to 5 
    limit: Annotated[int, Query(le=5)] = 5,
):
    brands_list = session.exec(
        select(Brand)
        .where(Brand.name.ilike(f"%{brand_name}%"))
        .order_by(Brand.name.asc())
        .offset(offset)
        .limit(limit)
    ).all()

    if brands_list is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to retrieve brands. List is null"
        )
    
    return brands_list

class CreateNewPartRequest(BaseModel):
    brand_id: int
    type_id: int
    submitted_by_id: int | None = None
    part_name: str
    part_number: str | None = None
    image_url: str | None = None
    description: str | None = None
    
@router.post("", response_model=PartResponse)
def create_new_part(
    request: CreateNewPartRequest,
    current_user: CurrentUserDep,
    session: SessionDep
):
    request.submitted_by_id = current_user.id
    new_part = Part.model_validate(request)
    
    session.add(new_part)
    session.commit()
    session.refresh(new_part)

    return new_part