from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional

from backend.gaia_genesis_new.core import data_manager as dm
from backend.database import get_db
from backend.gaia_genesis_new.api_v1 import schemas as api_schemas
from backend.gaia_genesis_new.logger import logger

router = APIRouter()

@router.post("/", response_model=api_schemas.ProductionData, status_code=status.HTTP_201_CREATED)
def add_production_data_entry( # Renamed to avoid conflict with schema name
    data_in: api_schemas.ProductionDataCreate,
    db: Session = Depends(get_db)
):
    manager = dm.DataManager(db)
    # DataManager already checks if well exists
    db_data = manager.add_production_data(data_in)
    if not db_data:
        logger.error(f"Failed to add production data for well ID {data_in.well_id}.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not add production data. Check if well exists."
        )
    return db_data

@router.post("/batch/", status_code=status.HTTP_201_CREATED) # Added trailing slash for consistency
def batch_add_production_data(
    data_in: List[api_schemas.ProductionDataCreate],
    db: Session = Depends(get_db)
):
    manager = dm.DataManager(db)
    if not data_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No production data provided in the batch."
        )

    # Optional: Add validation here to check if all well_ids in the batch exist
    # This could be performance intensive for very large batches.
    # For now, relying on DataManager's individual checks or DB constraints if any.

    count = manager.batch_create_production_data(data_in)
    if count != len(data_in):
        logger.warning(f"Batch production data creation partially failed. Expected {len(data_in)}, created {count}.")
        # Decide on appropriate response. 207 Multi-Status could be an option for partial success.
        # For simplicity, if not all are created, it might indicate an issue.
        # However, batch_create_production_data as implemented returns 0 on any error.
        if count == 0:
             raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Batch creation of production data failed entirely."
            )

    return {"message": f"Successfully added {count} production records.", "records_processed": count}


@router.get("/by_well/{well_id}", response_model=List[api_schemas.ProductionData])
def get_production_data_for_well( # Renamed to avoid conflict
    well_id: int,
    start_date: Optional[date] = Query(None, description="Start date for data retrieval (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for data retrieval (YYYY-MM-DD)"),
    skip: int = 0,
    limit: int = 1000, # Default limit for time-series data can be higher
    db: Session = Depends(get_db)
):
    manager = dm.DataManager(db)
    if not manager.get_well(well_id):
        logger.warning(f"Well ID {well_id} not found when trying to get production data.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Well with id {well_id} not found."
        )
    production_list = manager.get_production_data_for_well(
        well_id=well_id, start_date=start_date, end_date=end_date, skip=skip, limit=limit
    )
    return production_list

@router.delete("/{production_data_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_production_data_entry( # Renamed
    production_data_id: int,
    db: Session = Depends(get_db)
):
    manager = dm.DataManager(db)
    # Check existence first for proper 404
    # DataManager's delete_production_data returns bool, so we can use that
    success = manager.delete_production_data(production_data_id)
    if not success:
        # It could be not found, or another error. DataManager logs specifics.
        # For a simple API, we can just assume not found if delete returns false.
        logger.warning(f"Production data entry ID {production_data_id} not found for deletion.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Production data entry with id {production_data_id} not found."
        )
    return None
