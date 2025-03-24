
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import Annotated
from sqlmodel import select, Session
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from datetime import datetime, timezone 
from ..database import User, PartType
from ..models import BuildResponse
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