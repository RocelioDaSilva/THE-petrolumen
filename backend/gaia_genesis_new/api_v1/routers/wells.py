from fastapi import APIRouter, Depends, HTTPException, status, Path as FastApiPath # Alias Path to avoid conflict
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.gaia_genesis_new.core import data_manager as dm
from backend.database import get_db
from backend.gaia_genesis_new.api_v1 import schemas as api_schemas
from backend.gaia_genesis_new.logger import logger

router = APIRouter()

@router.post("/", response_model=api_schemas.Well, status_code=status.HTTP_201_CREATED)
def create_well(
    well_in: api_schemas.WellCreate,
    db: Session = Depends(get_db)
):
    manager = dm.DataManager(db)
    # DataManager's create_well already checks if reservoir exists
    db_well = manager.create_well(well_in)
    if not db_well:
        logger.error(f"Failed to create well '{well_in.name}'. Reservoir ID {well_in.reservoir_id} might be invalid.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create well. Check if reservoir exists or data is invalid."
        )
    return db_well

@router.get("/by_reservoir/{reservoir_id}", response_model=List[api_schemas.Well])
def get_wells_by_reservoir(
    reservoir_id: int = FastApiPath(..., gt=0, description="The ID of the reservoir to retrieve wells for"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    manager = dm.DataManager(db)
    # Check if reservoir exists first
    if not manager.get_reservoir(reservoir_id):
        logger.warning(f"Reservoir ID {reservoir_id} not found when trying to get its wells.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reservoir with id {reservoir_id} not found."
        )
    wells = manager.get_wells_by_reservoir(reservoir_id=reservoir_id, skip=skip, limit=limit)
    return wells

@router.get("/{well_id}", response_model=api_schemas.WellWithDetails) # Using richer schema
def get_well(
    well_id: int = FastApiPath(..., gt=0, description="The ID of the well to retrieve"),
    db: Session = Depends(get_db)
):
    manager = dm.DataManager(db)
    db_well = manager.get_well(well_id)
    if not db_well:
        logger.warning(f"Well ID {well_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Well with id {well_id} not found"
        )
    # Assuming WellWithDetails relationships (production_data, pvt_data) are handled by SQLAlchemy's ORM loading
    return db_well

@router.put("/{well_id}", response_model=api_schemas.Well)
def update_well(
    well_id: int,
    well_in: api_schemas.WellUpdate, # Using WellUpdate schema
    db: Session = Depends(get_db)
):
    manager = dm.DataManager(db)
    db_well = manager.update_well(well_id, well_in)
    if not db_well:
        # DataManager logs specifics. Check if it was simply not found.
        if manager.get_well(well_id) is None:
            logger.warning(f"Well ID {well_id} not found for update.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Well with id {well_id} not found"
            )
        else: # Other update error (e.g., target reservoir for move not found)
            logger.error(f"Failed to update well ID {well_id}.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not update well with id {well_id}. Target reservoir may be invalid."
            )
    return db_well

@router.delete("/{well_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_well(
    well_id: int,
    db: Session = Depends(get_db)
):
    manager = dm.DataManager(db)
    if not manager.get_well(well_id):
        logger.warning(f"Attempt to delete non-existent well ID {well_id}.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Well with id {well_id} not found"
        )

    success = manager.delete_well(well_id)
    if not success:
        logger.error(f"Failed to delete well ID {well_id} after existence check.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not delete well with id {well_id}"
        )
    return None # For 204 No Content response
