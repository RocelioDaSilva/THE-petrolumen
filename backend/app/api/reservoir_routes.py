"""Reservoir engineering API routes.

Exposes validated book calculations (Guo/Lyons/Ghalambor 2007) via
``app.engines.reservoir.ppes_bridge``. Mount in ``main.py`` with:

    from app.api.reservoir_routes import router as reservoir_router
    app.include_router(reservoir_router)
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.engines.reservoir.ppes_bridge import (
    vogel_rate, z_hall_yarborough, pseudo_critical_from_sg,
    exponential_rate, exponential_cum,
)

router = APIRouter(prefix="/api/v1/reservoir", tags=["reservoir"])


# ---------------------------------------------------------------------------
# Capability discovery
# ---------------------------------------------------------------------------
@router.get("/capabilities")
def capabilities():
    """List which book modules are wired into this router."""
    return {
        "engine": "ppes",
        "source": "Guo, Lyons, Ghalambor (2007)",
        "validated_examples": 29,
        "modules_exposed": [
            {"chapter": 2, "name": "PVT", "functions": ["z_hall_yarborough",
                                                       "pseudo_critical_from_sg"]},
            {"chapter": 3, "name": "IPR", "functions": ["vogel_rate"]},
            {"chapter": 8, "name": "Decline",
             "functions": ["exponential_rate", "exponential_cum"]},
        ],
    }


# ---------------------------------------------------------------------------
# Chapter 3 — Vogel IPR
# ---------------------------------------------------------------------------
class VogelRequest(BaseModel):
    qmax: float = Field(..., gt=0, description="Maximum rate [stb/day]")
    pwf: float = Field(..., ge=0, description="Flowing BHP [psia]")
    pbar: float = Field(..., gt=0, description="Average reservoir pressure [psia]")


class VogelResponse(BaseModel):
    q: float
    method: str = "vogel_eq_3_19"


@router.post("/vogel", response_model=VogelResponse)
def api_vogel(req: VogelRequest):
    """Chapter 3, Eq. 3.19 — Vogel IPR for a two-phase oil reservoir."""
    if req.pwf > req.pbar:
        raise HTTPException(400, "pwf must not exceed pbar")
    try:
        q = vogel_rate(req.qmax, req.pwf, req.pbar)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    return VogelResponse(q=q)


# ---------------------------------------------------------------------------
# Chapter 2 — z-factor from gas specific gravity
# ---------------------------------------------------------------------------
class ZFactorRequest(BaseModel):
    p: float = Field(..., gt=0, description="Pressure [psia]")
    t_F: float = Field(..., description="Temperature [F]")
    gamma_g: float = Field(..., gt=0, lt=2, description="Gas SG (air=1)")


class ZFactorResponse(BaseModel):
    z: float
    p_pr: float
    t_pr: float
    p_pc: float
    t_pc: float
    method: str = "hall_yarborough_eq_2_52_2_59"


@router.post("/z-factor", response_model=ZFactorResponse)
def api_z_factor(req: ZFactorRequest):
    """Chapter 2 — Hall-Yarborough z-factor with pseudo-critical lookup."""
    try:
        p_pc, t_pc = pseudo_critical_from_sg(req.gamma_g)
        t_R = req.t_F + 460.0
        p_pr = req.p / p_pc
        t_pr = t_R / t_pc
        z = z_hall_yarborough(p_pr, t_pr)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    return ZFactorResponse(z=z, p_pr=p_pr, t_pr=t_pr, p_pc=p_pc, t_pc=t_pc)


# ---------------------------------------------------------------------------
# Chapter 8 — Exponential decline
# ---------------------------------------------------------------------------
class ExponentialDeclineRequest(BaseModel):
    qi: float = Field(..., gt=0, description="Initial rate [stb/day]")
    b: float = Field(..., gt=0, description="Decline rate [/time]")
    t: float = Field(..., ge=0, description="Time [same units as b]")


class ExponentialDeclineResponse(BaseModel):
    q: float
    cumulative: float
    method: str = "exponential_eq_8_16_8_18"


@router.post("/decline/exponential", response_model=ExponentialDeclineResponse)
def api_exponential_decline(req: ExponentialDeclineRequest):
    """Chapter 8 — Exponential decline rate and cumulative production."""
    try:
        q = exponential_rate(req.qi, req.b, req.t)
        cum = exponential_cum(req.qi, req.b, req.t)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    return ExponentialDeclineResponse(q=q, cumulative=cum)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@router.get("/health")
def health():
    return {"status": "ok", "module": "reservoir", "engine": "ppes"}