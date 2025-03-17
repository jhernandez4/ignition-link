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

@router.get("/makes/{year}", response_model=list[str])
def get_makes_from_year(year: int, session: SessionDep):
    makes = session.exec(
        select(Vehicle.make)
        .where(Vehicle.year == year)
        .order_by(Vehicle.make.asc())
        .distinct()
    ).all()

    if not makes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to find makes for the year {year}"
        )

    return makes

@router.get("/models", response_model=list[str])
def get_models_from_year_and_make(year: int, make: str, session: SessionDep):
    models = session.exec(
        select(Vehicle.model)
        .where(Vehicle.year == year, Vehicle.make == make)
    ).all()

    if not models:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to find find models for the year {year} and make {make}"
        )

    return models