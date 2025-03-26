from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from sqlmodel import select, Session
from pydantic import BaseModel
from ..database import Vehicle
from ..dependencies import (
    get_session
)

router = APIRouter(
    prefix="/vehicles",
    tags=["vehicles"],
)

SessionDep = Annotated[Session, Depends(get_session)]

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

@router.get("/models", response_model=list[Vehicle])
def get_models_from_year_and_make(year: int, make: str, session: SessionDep):
    models = session.exec(
        select(Vehicle)
        .where(Vehicle.year == year, Vehicle.make == make)
        .order_by(Vehicle.model.asc())
    ).all()

    if not models:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to find find models for the year {year} and make {make}"
        )

    return models

class GetModelsRequest(BaseModel):
    model: str
    year: int | None = None

@router.get("/query-models", response_model=list[Vehicle])
def get_models_by_name(
    request: GetModelsRequest,
    session: SessionDep
):
    if request.year:
        models = session.exec(
            select(Vehicle)
            .where(Vehicle.year == request.year, Vehicle.model.ilike(f"%{request.model}%"))
        ).all()
    else:
        models = session.exec(
            select(Vehicle)
            .where(Vehicle.model.ilike(f"%{request.model}%"))
        ).all()

    if models is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            details="Failed to retrieve vehicles. List of vehicles is null"
        )

    return models