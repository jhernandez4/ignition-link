from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import Annotated
from sqlmodel import select, Session
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from datetime import datetime, timezone 
from ..database import Post, User, Vehicle
from ..models import UserResponse
from ..dependencies import (
    get_session, get_user_from_cookie, encode_model_to_json
)

router = APIRouter(
    prefix="/vehicles",
    tags=["vehicles"],
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUserDep = Annotated[Session, Depends(get_user_from_cookie)]

@router.get("/years", response_model=list[int])
def get_years_for_available_cars(session: SessionDep):
    years = session.exec(
        select(Vehicle.year)
        .distinct()
        .order_by(Vehicle.year.desc())
    ).all()

    if not years:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to find years for available cars"
        )

    return years
