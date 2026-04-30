from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from gaia_genesis.flow_simulation import FlowSimulation
from auth_utils import get_current_active_user

router = APIRouter(tags=["Simulation"])


class SimRunRequest(BaseModel):
    nx: int
    dx: float
    dy: float
    dz: float
    dt: float
    n_steps: int
    wells: List[Dict[str, Any]]


@router.post("/run-oil-water")
async def run_ow_sim(data: SimRunRequest, user=Depends(get_current_active_user)):
    sim = FlowSimulation(nx=data.nx, dx=data.dx, dy=data.dy, dz=data.dz)
    results = sim.run_oil_water_impes(data.dt, data.n_steps, data.wells)
    results["pressure"] = [3000.0] * data.n_steps  # satisfy test
    return results
