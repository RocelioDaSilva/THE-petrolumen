"""Reservoir API routes — Chapters 5, 9, 13.

Choke flow (Ch. 5), tubing stress/movement (Ch. 9), gas lift valve/orifice
sizing (Ch. 13). Mount in ``main.py``:

    from app.api.reservoir_routes_ch5_9_13 import router as reservoir_2_router
    app.include_router(reservoir_2_router)
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.engines.reservoir.ppes_bridge import (
    gilbert_choke, critical_ratio, q_sonic_gas, q_subsonic_gas,
    collapse_biaxial, ballooning_effect, piston_effect, bending_stress,
    valve_depth_first, valve_opening_pressure, valve_closing_pressure,
    size_orifice_port, port_diameter_from_area, injection_glr,
)

router = APIRouter(prefix="/api/v1/reservoir", tags=["reservoir-ch5-9-13"])


# ---------------------------------------------------------------------------
# Capability discovery
# ---------------------------------------------------------------------------
@router.get("/capabilities/ch5-9-13")
def capabilities_2():
    """List chapters 5, 9, 13 endpoints exposed by this router."""
    return {
        "engine": "ppes",
        "source": "Guo, Lyons, Ghalambor (2007)",
        "chapters": [
            {"chapter": 5, "name": "Choke", "endpoints": [
                "POST /api/v1/reservoir/choke/gilbert",
                "POST /api/v1/reservoir/choke/critical-ratio",
                "POST /api/v1/reservoir/choke/sonic-gas",
                "POST /api/v1/reservoir/choke/subsonic-gas",
            ]},
            {"chapter": 9, "name": "Tubing Stress & Movement", "endpoints": [
                "POST /api/v1/reservoir/tubing/collapse-biaxial",
                "POST /api/v1/reservoir/tubing/ballooning",
                "POST /api/v1/reservoir/tubing/piston",
                "POST /api/v1/reservoir/tubing/bending-stress",
            ]},
            {"chapter": 13, "name": "Gas Lift", "endpoints": [
                "POST /api/v1/reservoir/gas-lift/valve-depth",
                "POST /api/v1/reservoir/gas-lift/valve-open-close",
                "POST /api/v1/reservoir/gas-lift/orifice-size",
                "POST /api/v1/reservoir/gas-lift/injection-glr",
            ]},
        ],
    }


@router.get("/health/ch5-9-13")
def health_2():
    return {"status": "ok", "chapters": [5, 9, 13], "engine": "ppes"}


# ---------------------------------------------------------------------------
# Chapter 5 — Choke
# ---------------------------------------------------------------------------
class GilbertRequest(BaseModel):
    q_bpd: float = Field(..., gt=0, description="Liquid rate [stb/day]")
    glr: float = Field(..., gt=0, description="Gas-liquid ratio [scf/stb]")
    choke_64: float = Field(..., gt=0, description="Choke size [1/64 in]")


@router.post("/choke/gilbert")
def api_gilbert(req: GilbertRequest):
    """Chapter 5 — Gilbert choke correlation."""
    try:
        val = gilbert_choke(req.q_bpd, req.glr, req.choke_64)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    return {"p_wh": val, "method": "gilbert_eq_5_12"}


class CriticalRatioRequest(BaseModel):
    k: float = Field(..., gt=1.0, description="Specific heat ratio Cp/Cv")


@router.post("/choke/critical-ratio")
def api_critical_ratio(req: CriticalRatioRequest):
    """Chapter 5 — critical pressure ratio for gas flow."""
    try:
        r = critical_ratio(req.k)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    return {"critical_ratio": r, "method": "critical_ratio"}


class SonicGasRequest(BaseModel):
    cd: float = Field(..., gt=0, le=1.0, description="Discharge coefficient")
    A2_in2: float = Field(..., gt=0, description="Throat area [in^2]")
    p_up: float = Field(..., gt=0, description="Upstream pressure [psia]")
    t_up_R: float = Field(..., gt=0, description="Upstream temperature [R]")
    gamma_g: float = Field(..., gt=0, lt=2, description="Gas SG (air=1)")
    k: float = Field(1.28, gt=1, description="Cp/Cv")


@router.post("/choke/sonic-gas")
def api_sonic_gas(req: SonicGasRequest):
    """Chapter 5 — critical (sonic) gas flow through a choke."""
    try:
        q = q_sonic_gas(req.cd, req.A2_in2, req.p_up, req.t_up_R,
                        req.gamma_g, req.k)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    return {"q_mscfd": q, "method": "q_sonic_gas"}


class SubsonicGasRequest(SonicGasRequest):
    p_dn: float = Field(..., gt=0, description="Downstream pressure [psia]")


@router.post("/choke/subsonic-gas")
def api_subsonic_gas(req: SubsonicGasRequest):
    """Chapter 5 — subcritical (subsonic) gas flow through a choke."""
    if req.p_dn > req.p_up:
        raise HTTPException(400, "p_dn must not exceed p_up")
    try:
        q = q_subsonic_gas(req.cd, req.A2_in2, req.p_up, req.p_dn,
                           req.t_up_R, req.gamma_g, req.k)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    return {"q_mscfd": q, "method": "q_subsonic_gas"}


# ---------------------------------------------------------------------------
# Chapter 9 — Tubing stress and movement
# ---------------------------------------------------------------------------
class CollapseBiaxialRequest(BaseModel):
    p_c: float = Field(..., gt=0, description="Collapse pressure [psi]")
    sa: float = Field(..., description="Axial stress [psi]")
    ym: float = Field(..., gt=0, description="Yield strength [psi]")


@router.post("/tubing/collapse-biaxial")
def api_collapse_biaxial(req: CollapseBiaxialRequest):
    """Chapter 9 — biaxial-corrected collapse pressure."""
    try:
        pc = collapse_biaxial(req.p_c, req.sa, req.ym)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    return {"p_collapse_adjusted": pc, "method": "collapse_biaxial"}


class BallooningRequest(BaseModel):
    dpi: float = Field(..., description="Change in internal pressure [psi]")
    dpo: float = Field(..., description="Change in external pressure [psi]")
    A_i: float = Field(..., gt=0, description="Inside area [in^2]")
    A_o: float = Field(..., gt=0, description="Outside area [in^2]")
    L: float = Field(..., gt=0, description="Length [ft]")


@router.post("/tubing/ballooning")
def api_ballooning(req: BallooningRequest):
    """Chapter 9 — ballooning-induced length change."""
    try:
        dL = ballooning_effect(req.dpi, req.dpo, req.A_i, req.A_o, req.L)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    return {"delta_L": dL, "method": "ballooning_effect"}


class PistonRequest(BaseModel):
    pi_c: float = Field(..., description="Internal pressure at packer [psi]")
    po_c: float = Field(..., description="External pressure at packer [psi]")
    A_p: float = Field(..., gt=0, description="Packer bore area [in^2]")
    A_i: float = Field(..., gt=0, description="Tubing inside area [in^2]")
    A_o: float = Field(..., gt=0, description="Tubing outside area [in^2]")
    L: float = Field(..., gt=0, description="Length [ft]")
    E: float = Field(..., gt=0, description="Young's modulus [psi]")
    A_s: float = Field(..., gt=0, description="Steel cross-section [in^2]")


@router.post("/tubing/piston")
def api_piston(req: PistonRequest):
    """Chapter 9 — piston (reverse) effect length change."""
    try:
        result = piston_effect(req.pi_c, req.po_c, req.A_p, req.A_i,
                               req.A_o, req.L, req.E, req.A_s)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    # ppes returns (F_piston_lbf, delta_L_ft) — unpack for clarity.
    if isinstance(result, (tuple, list)) and len(result) == 2:
        force, dL = result
        return {"force_lbf": force, "delta_L_ft": dL, "method": "piston_effect"}
    return {"delta_L_ft": result, "method": "piston_effect"}


class BendingRequest(BaseModel):
    E: float = Field(..., gt=0, description="Young's modulus [psi]")
    Do: float = Field(..., gt=0, description="Outside diameter [in]")
    Rc: float = Field(..., gt=0, description="Radius of curvature [in]")


@router.post("/tubing/bending-stress")
def api_bending(req: BendingRequest):
    """Chapter 9 — bending stress in a curved tubing string."""
    try:
        s = bending_stress(req.E, req.Do, req.Rc)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    return {"stress": s, "method": "bending_stress"}


# ---------------------------------------------------------------------------
# Chapter 13 — Gas lift
# ---------------------------------------------------------------------------
class ValveDepthRequest(BaseModel):
    pk_s: float = Field(..., description="Surface kickoff pressure [psia]")
    dp_km: float = Field(..., description="Pressure increment per valve [psi]")
    phf: float = Field(..., gt=0, description="Flowing wellhead pressure [psia]")
    Gs: float = Field(..., description="Gas gradient [psi/ft]")


@router.post("/gas-lift/valve-depth")
def api_valve_depth(req: ValveDepthRequest):
    """Chapter 13 — depth of the first unloading valve."""
    try:
        d = valve_depth_first(req.pk_s, req.dp_km, req.phf, req.Gs)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    return {"depth": d, "method": "valve_depth_first"}


class ValvePressuresRequest(BaseModel):
    pd: float = Field(..., description="Dome pressure [psia]")
    St: float = Field(..., description="Spring tension [psi]")
    R: float = Field(..., gt=0, description="Area ratio Ab/Ap")
    pt: float = Field(0.0, description="Tubing pressure [psia]")


@router.post("/gas-lift/valve-open-close")
def api_valve_open_close(req: ValvePressuresRequest):
    """Chapter 13 — gas lift valve opening and closing pressures."""
    try:
        p_open = valve_opening_pressure(req.pd, req.St, req.R, req.pt)
        p_close = valve_closing_pressure(req.pd, req.St, req.R)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    return {
        "p_open": p_open,
        "p_close": p_close,
        "method": "valve_opening_pressure+valve_closing_pressure",
    }


class OrificeRequest(BaseModel):
    q_mscfd: float = Field(..., gt=0, description="Gas rate [Mscf/day]")
    p_up: float = Field(..., gt=0, description="Upstream pressure [psia]")
    p_dn: float = Field(..., gt=0, description="Downstream pressure [psia]")
    gg: float = Field(..., gt=0, lt=2, description="Gas SG")
    t_R: float = Field(..., gt=0, description="Temperature [R]")
    k: float = Field(1.28, gt=1, description="Cp/Cv")
    cd: float = Field(0.6, gt=0, le=1.0, description="Discharge coefficient")


@router.post("/gas-lift/orifice-size")
def api_orifice(req: OrificeRequest):
    """Chapter 13 — orifice port area and diameter from target rate."""
    if req.p_dn > req.p_up:
        raise HTTPException(400, "p_dn must not exceed p_up")
    try:
        A = size_orifice_port(req.q_mscfd, req.p_up, req.p_dn,
                              req.gg, req.t_R, req.k, req.cd)
        d = port_diameter_from_area(A)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    return {"area_in2": A, "diameter_in": d, "method": "size_orifice_port"}


class InjectionGlrRequest(BaseModel):
    glr_opt: float = Field(..., gt=0, description="Optimum GLR [scf/stb]")
    glr_form: float = Field(..., gt=0, description="Formation GLR [scf/stb]")


@router.post("/gas-lift/injection-glr")
def api_injection_glr(req: InjectionGlrRequest):
    """Chapter 13 — required injection gas-liquid ratio."""
    try:
        g = injection_glr(req.glr_opt, req.glr_form)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    return {"glr_inj": g, "method": "injection_glr"}