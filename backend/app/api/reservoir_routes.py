"""Reservoir engineering API routes.

Exposes validated book calculations (Guo/Lyons/Ghalambor 2007) via
``app.engines.reservoir.ppes_bridge``. Mount in ``main.py`` with:

    from app.api.reservoir_routes import router as reservoir_router
    app.include_router(reservoir_router)
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import Field

from .base import APIModel as BaseModel

from app.engines.reservoir.ppes_bridge import (
    vogel_rate, z_hall_yarborough, pseudo_critical_from_sg,
    exponential_rate, exponential_cum,
)

router = APIRouter(prefix="/api/v1/reservoir", tags=["reservoir"])


class ReservoirModuleCapability(BaseModel):
    chapter: int
    name: str
    functions: list[str]


class ReservoirCalculationCapability(BaseModel):
    name: str
    endpoint: str
    status: Literal["available", "limited", "planned"]
    limitations: list[str]


class ReservoirCapabilitiesResponse(BaseModel):
    engine: str
    source: str
    validated_examples: int
    modules_exposed: list[ReservoirModuleCapability]
    additional_calculations: list[ReservoirCalculationCapability]
    catalog_scope: str
    product_scope: str
    not_intended_for: list[str]


class ReservoirHealthResponse(BaseModel):
    status: Literal["ok"]
    module: str
    engine: str


# ---------------------------------------------------------------------------
# Capability discovery
# ---------------------------------------------------------------------------
@router.get("/capabilities", response_model=ReservoirCapabilitiesResponse)
def capabilities() -> ReservoirCapabilitiesResponse:
    """List available reservoir calculations and state their limitations."""
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
        "additional_calculations": [
            {
                "name": "Rock pore-volume compressibility",
                "endpoint": "/api/engine/reservoir/compressibility/rock",
                "status": "available",
                "limitations": [
                    "Newman's correlations are limited to consolidated sandstone "
                    "and limestone.",
                    "The published porosity interval is reported; strict mode "
                    "must be enabled to reject out-of-range values.",
                ],
            },
            {
                "name": "Gas isothermal compressibility",
                "endpoint": "/api/engine/reservoir/compressibility/gas",
                "status": "available",
                "limitations": [
                    "Uses the project's Hall-Yarborough Z correlation with Sutton "
                    "pseudocritical properties, not the book's DAK example curve.",
                    "Numerical differentiation is sensitive to the selected "
                    "pressure step and correlation convergence.",
                ],
            },
            {
                "name": "Total compressibility",
                "endpoint": "/api/engine/reservoir/compressibility/total",
                "status": "available",
                "limitations": [
                    "Oil and water compressibilities are user supplied.",
                    "The phase-weighted relation assumes saturations sum to one.",
                ],
            },
        ],
        "catalog_scope": "This list supplements the ppes modules exposed by "
        "this router; it is not an exhaustive inventory of all API routes.",
        "product_scope": "Engineering calculations and transparent technical "
        "decision support.",
        "not_intended_for": [
            "ERP, accounting, or corporate financial management",
            "Autonomous engineering decisions without qualified review",
            "Regulatory compliance certification",
            "Replacement for validated commercial full-field simulation",
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
class VogelCurveRequest(BaseModel):
    qmax: float = Field(..., gt=0, description="Maximum rate [stb/day]")
    pbar: float = Field(..., gt=0, description="Average reservoir pressure [psia]")
    n_points: int = Field(25, ge=2, le=1000, description="Sweep points")


class VogelCurvePoint(BaseModel):
    q: float
    pwf: float


class VogelCurveResponse(BaseModel):
    points: list[VogelCurvePoint]
    method: str = "vogel_eq_3_19_inverse"


@router.post("/vogel/curve", response_model=VogelCurveResponse)
def api_vogel_curve(req: VogelCurveRequest):
    """Chapter 3 - batch Vogel IPR sweep (q -> pwf, closed-form inverse)."""
    n = req.n_points
    dq = req.qmax / (n - 1)
    pts = []
    for i in range(n):
        q = i * dq
        ratio = min(0.999, q / req.qmax)
        pwf = max(0.0, 0.125 * req.pbar * (-1.0 + (81.0 - 80.0 * ratio) ** 0.5))
        pts.append(VogelCurvePoint(q=round(q, 2), pwf=round(pwf, 2)))
    return VogelCurveResponse(points=pts)


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
@router.get("/health", response_model=ReservoirHealthResponse)
def health() -> ReservoirHealthResponse:
    return ReservoirHealthResponse(
        status="ok", module="reservoir", engine="ppes"
    )