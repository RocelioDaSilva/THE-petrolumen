from fastapi import APIRouter, Depends, HTTPException, Path
import pandas as pd
from auth_utils import get_current_active_user
from ...core.database_manager import DatabaseManager
from ...surveillance import calculate_ratios

router = APIRouter()


@router.get("/ratios/{well_name}")
async def get_production_ratios(
    well_name: str = Path(...), user=Depends(get_current_active_user)
):
    db = DatabaseManager.get_instance()
    well = db.get_well_by_name(well_name)
    if not well:
        raise HTTPException(status_code=404, detail="Well not found")

    data = db.get_well_production_data(well.id)
    if not data:
        return {"data": []}

    df = pd.DataFrame(data)
    df = calculate_ratios(df)
    return df.to_dict(orient="records")
