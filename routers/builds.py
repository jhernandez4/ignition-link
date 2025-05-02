from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import Annotated
from sqlmodel import select, Session, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from datetime import datetime, timezone 
from ..database import User, Vehicle, Build, Part, PartType, BuildPartLink
from ..models import BuildResponse, BuildWithPartsResponse
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

class EditBuildInfoRequest(BaseModel):
    nickname: str | None = None
    cover_picture_url: str | None = None
    description: str | None = None

@router.get("/all", response_model=list[BuildResponse])
def get_all_builds(
    session: SessionDep,
    offset: int = 0,
    # Less than or equal to 100; default to 100
    limit: Annotated[int, Query(le=100)] = 100,
):
    builds_list = session.exec(
        select(Build)
        .offset(offset)
        .limit(limit)
        .order_by(Build.id.desc())
    ).all()

    if builds_list is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to get builds. Builds list is none"
        )

    return builds_list

@router.patch("/{build_id}", response_model=BuildResponse)
def edit_build_info(
    build_id: int,
    request: EditBuildInfoRequest,
    current_user: CurrentUserDep,
    session: SessionDep
):
    build_to_edit = session.exec(
        select(Build)
        .where(Build.id == build_id)
    ).first()

    if not build_to_edit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to retrieve build. Build with id {build_id} does not exist."
        )
    
    if build_to_edit.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to edit build. You do not have permission to edit this build."
        )
    
    # exclude_unset excludes values that were not sent by the client 
    build_data = request.model_dump(exclude_unset=True)

    # update build object with new edit data
    build_to_edit.sqlmodel_update(build_data)

    session.add(build_to_edit)
    session.commit()
    session.refresh(build_to_edit)

    return build_to_edit

@router.get("/{build_id}", response_model=BuildWithPartsResponse)
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

@router.delete("/{build_id}")
def delete_build_by_id(
    build_id: int,
    session: SessionDep,
    current_user: CurrentUserDep
):
    build_to_delete = session.exec(
        select(Build)
        .where(Build.id == build_id)
    ).first()

    if not build_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to delete build. Build with id {build_id} does not exist."
        )
    
    if build_to_delete.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to delete build. You do not have permission to delete this build."
        )
    
    session.delete(build_to_delete)
    session.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": f"Successfully deleted build with id {build_id}"
        }
    )

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

@router.delete("/{build_id}/part/{part_id}", response_model=BuildWithPartsResponse)
def remove_part_from_build(
    build_id: int,
    part_id: int,
    session: SessionDep,
    current_user: CurrentUserDep
):
    part_to_remove = session.exec(
       select(Part)
       .where(Part.id == part_id)
    ).first()

    if not part_to_remove:
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail=f"Failed to remove part from build. Part with id {part_id} not found"
       )
   
    build_to_edit = session.exec(
        select(Build)
        .where(Build.id == build_id)
    ).first()

    if not build_to_edit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to remove part from build. Build with id {build_id} not found"
        )
    
    if build_to_edit.user_id != current_user.id:
       raise HTTPException(
           status_code=status.HTTP_401_UNAUTHORIZED,
           detail="Failed to remove part from build. You are not the owner of this build"
       )
    
    if part_to_remove not in build_to_edit.parts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to remove part from build. Part is not on this build"
        )
    
    build_to_edit.parts.remove(part_to_remove)

    session.add(build_to_edit)
    session.commit()
    session.refresh(build_to_edit)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": f"Successfully removed part with id {part_id} from build"
        }
    ) 
    
@router.patch("/{build_id}/part/{part_id}", response_model=BuildWithPartsResponse)
def add_part_to_build(
    build_id: int,
    part_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    part_to_add = session.exec(
        select(Part)
        .where(Part.id == part_id)
    ).first()

    if not part_to_add:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to add part to build. Part with id {part_id} not found"
        )
    
    build_to_edit = session.exec(
        select(Build)
        .where(Build.id == build_id)
    ).first()

    if not build_to_edit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to add part to build. Build with build id {build_id} not found"
        )
    
    if build_to_edit.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to add part to build. You are not the owner of this build"
        )

    if part_to_add in build_to_edit.parts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to to add part to build. Part is already on this build"
        )

    build_to_edit.parts.append(part_to_add)
    
    session.add(build_to_edit)
    session.commit()
    session.refresh(build_to_edit)

    return build_to_edit

@router.get("/{build_id}/part-categories")
def get_build_part_categories(
    build_id: int,
    session: SessionDep
):
    part_categories = session.exec(
        select(
            PartType.type, # Category name
            func.count(Part.id) # Count of parts in this category
        )
        .join(Part, Part.type_id == PartType.id)
        .join(BuildPartLink, BuildPartLink.part_id == Part.id)
        .where(BuildPartLink.build_id == build_id)
        .group_by(PartType.type)
    ).all()


    categories = [
        {"name": part_type, "count": count}
        for part_type, count in part_categories
    ]

    # Calculate the total count of all parts (for "All" category)
    total_parts = sum(category["count"] for category in categories)

    # Insert the "All" category at the beginning
    categories.insert(0, {"name": "All", "count": total_parts})

    return categories