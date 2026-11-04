"""Reservoir API — Chapter 2 PVT extensions.

Black-oil and gas property correlations from ppes.ch02_pvt, exposed over
HTTP via ppes_bridge. Mount in ``main.py``:

    from app.api.reservoir_routes_pvt import router as reservoir_pvt_router
    app.include_router(reservoir_pvt_router)
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.engines.reservoir.ppes_bridge import (
    rs_standing, bo_standing,
    mu_dead_oil, mu_sat_oil, mu_unsat_oil, mu_gas_low_pressure,
    rho_o, rho_gas, bg, eg,
    oil_compressibility, wichert_aziz_correction,
    z_brill_beggs, pseudo_critical_from_sg,
)

router = APIRouter(prefix="/api/v1/reservoir", tags=["reservoir-pvt"])


def _call(fn, model):
    """Unpack pydantic model into fn kwargs, mapping any exception to 400."""
    try:
        return fn(**model.model_dump())
    except Exception as exc:
        raise HTTPException(400, str(exc))


@router.get("/capabilities/pvt")
def capabilities_pvt():
    return {
        "engine": "ppes",
        "source": "Guo, Lyons, Ghalambor (2007) - Chapter 2 PVT",
        "endpoints": [
            "POST /pvt/rs-standing", "POST /pvt/bo-standing",
            "POST /pvt/mu-dead-oil", "POST /pvt/mu-sat-oil",
            "POST /pvt/mu-unsat-oil", "POST /pvt/mu-gas-low-pressure",
            "POST /pvt/rho-oil", "POST /pvt/rho-gas",
            "POST /pvt/bg", "POST /pvt/eg",
            "POST /pvt/oil-compressibility", "POST /pvt/wichert-aziz",
            "POST /pvt/z-brill-beggs",
        ],
    }


@router.get("/health/pvt")
def health_pvt():
    return {"status": "ok", "chapter": 2, "engine": "ppes"}


class RsRequest(BaseModel):
    p: float = Field(..., gt=0, description="Pressure [psia]")
    t_F: float = Field(..., description="Temperature [F]")
    api: float = Field(..., gt=0, description="Oil API gravity")
    gamma_g: float = Field(..., gt=0, lt=2, description="Gas SG (air=1)")

@router.post("/pvt/rs-standing")
def api_rs(req: RsRequest):
    """Standing Rs — solution gas-oil ratio [scf/stb]."""
    return {"rs": _call(rs_standing, req), "method": "rs_standing"}


class BoRequest(BaseModel):
    t_F: float = Field(..., description="Temperature [F]")
    api: float = Field(..., gt=0)
    rs: float = Field(..., ge=0, description="Solution GOR [scf/stb]")
    gamma_g: float = Field(..., gt=0, lt=2)

@router.post("/pvt/bo-standing")
def api_bo(req: BoRequest):
    """Standing Bo — oil FVF [rb/stb]."""
    return {"bo": _call(bo_standing, req), "method": "bo_standing"}


class MuDeadRequest(BaseModel):
    api: float = Field(..., gt=0)
    t_F: float = Field(...)

@router.post("/pvt/mu-dead-oil")
def api_mu_dead(req: MuDeadRequest):
    """Dead oil viscosity [cp]."""
    return {"mu_od": _call(mu_dead_oil, req), "method": "mu_dead_oil"}


class MuSatRequest(BaseModel):
    rs: float = Field(..., ge=0)
    mu_od: float = Field(..., gt=0, description="Dead oil viscosity [cp]")

@router.post("/pvt/mu-sat-oil")
def api_mu_sat(req: MuSatRequest):
    """Saturated oil viscosity [cp]."""
    return {"mu_ob": _call(mu_sat_oil, req), "method": "mu_sat_oil"}


class MuUnsatRequest(BaseModel):
    p: float = Field(..., gt=0)
    pb: float = Field(..., gt=0, description="Bubble point [psia]")
    mu_od: float = Field(..., gt=0)
    mu_ob: float = Field(..., gt=0)

@router.post("/pvt/mu-unsat-oil")
def api_mu_unsat(req: MuUnsatRequest):
    """Undersaturated oil viscosity [cp]."""
    return {"mu_o": _call(mu_unsat_oil, req), "method": "mu_unsat_oil"}


class MuGasRequest(BaseModel):
    gamma_g: float = Field(..., gt=0, lt=2)
    t_R: float = Field(..., gt=0, description="Temperature [R]")
    y_N2: float = Field(0.0, ge=0, le=1)
    y_CO2: float = Field(0.0, ge=0, le=1)
    y_H2S: float = Field(0.0, ge=0, le=1)

@router.post("/pvt/mu-gas-low-pressure")
def api_mu_gas(req: MuGasRequest):
    """Gas viscosity at low pressure [cp]."""
    return {"mu_g": _call(mu_gas_low_pressure, req), "method": "mu_gas_low_pressure"}


class RhoOilRequest(BaseModel):
    p: float = Field(..., gt=0)
    t_F: float = Field(...)
    api: float = Field(..., gt=0)
    rs: float = Field(..., ge=0)
    gamma_g: float = Field(..., gt=0, lt=2)

@router.post("/pvt/rho-oil")
def api_rho_oil(req: RhoOilRequest):
    """Live oil density [lb/ft^3]. Book Example 2.1 returns 44.9."""
    return {"rho_o": _call(rho_o, req), "method": "rho_o"}


class RhoGasRequest(BaseModel):
    p: float = Field(..., gt=0)
    t_R: float = Field(..., gt=0)
    gamma_g: float = Field(..., gt=0, lt=2)
    z: float = Field(..., gt=0, description="Compressibility factor")

@router.post("/pvt/rho-gas")
def api_rho_gas(req: RhoGasRequest):
    """Gas density [lb/ft^3]."""
    return {"rho_g": _call(rho_gas, req), "method": "rho_gas"}


class BgRequest(BaseModel):
    p: float = Field(..., gt=0)
    t_R: float = Field(..., gt=0)
    z: float = Field(..., gt=0)

@router.post("/pvt/bg")
def api_bg(req: BgRequest):
    """Gas FVF Bg [rb/scf]."""
    return {"bg": _call(bg, req), "method": "bg"}

@router.post("/pvt/eg")
def api_eg(req: BgRequest):
    """Gas expansion factor Eg [scf/rb] (= 1/Bg)."""
    return {"eg": _call(eg, req), "method": "eg"}


class CoRequest(BaseModel):
    p: float = Field(..., gt=0)
    rs: float = Field(..., ge=0)
    t_F: float = Field(...)
    api: float = Field(..., gt=0)
    gamma_g: float = Field(..., gt=0, lt=2)

@router.post("/pvt/oil-compressibility")
def api_co(req: CoRequest):
    """Oil compressibility [1/psi]."""
    return {"co": _call(oil_compressibility, req), "method": "oil_compressibility"}


class WazRequest(BaseModel):
    y_H2S: float = Field(..., ge=0, le=1)
    y_CO2: float = Field(..., ge=0, le=1)
    p_pc: float = Field(..., gt=0)
    t_pc: float = Field(..., gt=0)

@router.post("/pvt/wichert-aziz")
def api_waz(req: WazRequest):
    """Wichert-Aziz sour-gas pseudocritical correction.

    Function may return a tuple or dict — surfaced verbatim as ``result``.
    """
    try:
        p_new, t_new = wichert_aziz_correction(
            req.y_H2S, req.y_CO2, req.p_pc, req.t_pc)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    # ppes returns (p_pc_corrected, t_pc_corrected) — unpack for clarity.
    return {"p_pc_corrected": p_new, "t_pc_corrected": t_new,
            "method": "wichert_aziz_correction"}


class ZBrillRequest(BaseModel):
    p: float = Field(..., gt=0, description="Pressure [psia]")
    t_F: float = Field(..., description="Temperature [F]")
    gamma_g: float = Field(..., gt=0, lt=2)

@router.post("/pvt/z-brill-beggs")
def api_z_brill(req: ZBrillRequest):
    """Brill-Beggs z-factor with pseudo-critical lookup.

    Convenience wrapper matching the shape of the existing /z-factor endpoint.
    """
    try:
        ppc, tpc = pseudo_critical_from_sg(req.gamma_g)
        p_pr = req.p / ppc
        t_pr = (req.t_F + 460.0) / tpc
        z = z_brill_beggs(p_pr, t_pr)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    return {"z": z, "p_pr": p_pr, "t_pr": t_pr,
            "p_pc": ppc, "t_pc": tpc, "method": "z_brill_beggs"}