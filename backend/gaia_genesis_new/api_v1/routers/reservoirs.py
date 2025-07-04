from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

# Use aliased imports for clarity
from backend.gaia_genesis_new.core import data_manager as dm
from backend.database import get_db # Assuming get_db is in backend/database.py
from backend.gaia_genesis_new.api_v1 import schemas as api_schemas
from backend.gaia_genesis_new.logger import logger

router = APIRouter()

@router.post("/", response_model=api_schemas.Reservoir, status_code=status.HTTP_201_CREATED)
def create_reservoir(
    reservoir_in: api_schemas.ReservoirCreate,
    db: Session = Depends(get_db)
):
    manager = dm.DataManager(db)
    # Check if reservoir with the same name already exists
    existing_reservoir = manager.get_reservoir_by_name(reservoir_in.name)
    if existing_reservoir:
        logger.warning(f"Attempt to create reservoir with duplicate name: {reservoir_in.name}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Reservoir with name '{reservoir_in.name}' already exists."
        )

    db_reservoir = manager.create_reservoir(reservoir_in)
    if not db_reservoir:
        logger.error(f"Failed to create reservoir: {reservoir_in.name}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create reservoir. Check for invalid data."
        )
    return db_reservoir

@router.get("/", response_model=List[api_schemas.Reservoir])
def get_all_reservoirs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    manager = dm.DataManager(db)
    reservoirs = manager.get_all_reservoirs(skip=skip, limit=limit)
    return reservoirs

@router.get("/{reservoir_id}", response_model=api_schemas.ReservoirWithDetails) # Using richer schema
def get_reservoir(
    reservoir_id: int,
    db: Session = Depends(get_db)
):
    manager = dm.DataManager(db)
    db_reservoir = manager.get_reservoir(reservoir_id)
    if not db_reservoir:
        logger.warning(f"Reservoir with ID {reservoir_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reservoir with id {reservoir_id} not found"
        )
    # Here you could load related wells and simulations if ReservoirWithDetails expects them
    # For now, assuming DataManager.get_reservoir might already load them if relationships are eager,
    # or they will be loaded on access due to lazy loading (check SQLAlchemy model relationship settings).
    # If you need to explicitly load, you would do it here. Example:
    # db_reservoir.wells = manager.get_wells_by_reservoir(reservoir_id) # If not automatically loaded
    return db_reservoir

@router.put("/{reservoir_id}", response_model=api_schemas.Reservoir)
def update_reservoir(
    reservoir_id: int,
    reservoir_in: api_schemas.ReservoirUpdate, # Using ReservoirUpdate schema
    db: Session = Depends(get_db)
):
    manager = dm.DataManager(db)
    # Check for name conflict if name is being changed
    if reservoir_in.name is not None:
        existing_reservoir = manager.get_reservoir_by_name(reservoir_in.name)
        if existing_reservoir and existing_reservoir.id != reservoir_id:
            logger.warning(f"Attempt to update reservoir ID {reservoir_id} with duplicate name: {reservoir_in.name}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Another reservoir with name '{reservoir_in.name}' already exists."
            )

    db_reservoir = manager.update_reservoir(reservoir_id, reservoir_in)
    if not db_reservoir:
        # This could be due to not found, or an SQLAlchemy error during update
        # DataManager logs specifics. If it's simply not found:
        if manager.get_reservoir(reservoir_id) is None:
             logger.warning(f"Reservoir with ID {reservoir_id} not found for update.")
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reservoir with id {reservoir_id} not found"
            )
        else: # Other update error
            logger.error(f"Failed to update reservoir ID {reservoir_id}.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, # Or 500 if it's an internal server error
                detail=f"Could not update reservoir with id {reservoir_id}"
            )
    return db_reservoir

@router.delete("/{reservoir_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reservoir(
    reservoir_id: int,
    db: Session = Depends(get_db)
):
    manager = dm.DataManager(db)
    # First check if it exists to return 404 if not
    if not manager.get_reservoir(reservoir_id):
        logger.warning(f"Attempt to delete non-existent reservoir ID {reservoir_id}.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reservoir with id {reservoir_id} not found"
        )

    success = manager.delete_reservoir(reservoir_id)
    if not success:
        # This case might be rare if the above check passes and cascade delete works,
        # unless there's a specific database constraint or error during deletion.
        logger.error(f"Failed to delete reservoir ID {reservoir_id} after existence check.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Or 400 if it's a known constraint
            detail=f"Could not delete reservoir with id {reservoir_id}"
        )
    return None # For 204 No Content response
