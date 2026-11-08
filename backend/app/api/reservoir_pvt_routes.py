"""Book-based black-oil and formation-water PVT API."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from app.engines.reservoir.black_oil_pvt import (
    gas_viscosity,
    oil_compressibility,
    oil_formation_volume_factor,
    oil_solution_gor,
    oil_viscosity,
    water_pvt,
)

router = APIRouter()


class GasViscosityRequest(BaseModel):
    p_psia: float = Field(gt=0.0, allow_inf_nan=False)
    temperature_f: float = Field(gt=-459.67, allow_inf_nan=False)
    z_factor: float = Field(gt=0.0, allow_inf_nan=False)
    gas_sg: float | None = Field(default=None, gt=0.0, lt=2.0, allow_inf_nan=False)
    molecular_weight_g_mol: float | None = Field(
        default=None, gt=0.0, allow_inf_nan=False
    )

    @model_validator(mode="after")
    def require_one_gas_composition_input(self) -> "GasViscosityRequest":
        if (self.gas_sg is None) == (self.molecular_weight_g_mol is None):
            raise ValueError(
                "Provide exactly one of gas_sg or molecular_weight_g_mol"
            )
        return self


class GasViscosityResponse(BaseModel):
    mu_g_cp: float
    rho_g_g_cm3: float
    molecular_weight_g_mol: float
    z_factor: float
    k_factor: float
    x_factor: float
    y_factor: float
    in_validity_range: bool
    correlation: Literal["lee_gonzalez_eakin"] = "lee_gonzalez_eakin"


class OilRequest(BaseModel):
    p_psia: float = Field(gt=0.0, allow_inf_nan=False)
    pb_psia: float = Field(gt=0.0, allow_inf_nan=False)
    temperature_f: float = Field(gt=-459.67, allow_inf_nan=False)
    gas_sg: float = Field(gt=0.0, lt=2.0, allow_inf_nan=False)
    oil_api: float = Field(gt=-10.0, lt=100.0, allow_inf_nan=False)


class OilRsoResponse(BaseModel):
    rso_scf_stb: float
    y_g: float
    clamped: bool
    in_validity_range: bool
    correlation: Literal["standing_beggs"] = "standing_beggs"


class OilBoRequest(OilRequest):
    co_psi_inv: float | None = Field(default=None, gt=0.0, allow_inf_nan=False)


class OilBoResponse(BaseModel):
    bo_bbl_stb: float
    f_term: float
    oil_specific_gravity: float
    rso_scf_stb: float
    clamped: bool
    in_validity_range: bool
    co_used_psi_inv: float | None
    correlation: Literal["standing_beggs"] = "standing_beggs"


class OilCompressibilityResponse(BaseModel):
    co_psi_inv: float
    formulation: Literal["villena_lanzi", "vasquez_beggs"]
    rsob_scf_stb: float
    in_validity_range: bool


class OilViscosityResponse(BaseModel):
    mu_o_cp: float
    mu_dead_cp: float
    mu_at_bubble_point_cp: float
    a_factor: float
    b_factor: float
    m_exponent: float | None
    formulation: Literal["beggs_robinson", "vasquez_beggs"]
    rso_scf_stb: float
    in_validity_range: bool


class WaterPVTRequest(BaseModel):
    p_psia: float = Field(gt=0.0, allow_inf_nan=False)
    temperature_f: float = Field(gt=0.0, allow_inf_nan=False)
    salinity_pct: float = Field(gt=0.0, lt=40.0, allow_inf_nan=False)
    c_nacl_g_l: float | None = Field(
        default=None, ge=0.0, le=200.0, allow_inf_nan=False
    )


class WaterPVTResponse(BaseModel):
    bw_bbl_stb: float
    rswp_scf_stb: float
    rsw_scf_stb: float
    cw_psi_inv: float
    mu_w_cp: float
    bw_in_validity_range: bool | None
    rsw_in_validity_range: bool
    cw_in_validity_range: bool
    mu_w_in_validity_range: bool


@router.post(
    "/engine/reservoir/pvt/gas-viscosity",
    tags=["Reservoir"],
    response_model=GasViscosityResponse,
    summary="Lee-Gonzalez-Eakin gas viscosity",
)
def calculate_gas_viscosity(
    payload: GasViscosityRequest,
) -> GasViscosityResponse:
    try:
        result = gas_viscosity(
            p_psia=payload.p_psia,
            temperature_f=payload.temperature_f,
            z_factor=payload.z_factor,
            gas_sg=payload.gas_sg,
            molecular_weight_g_mol=payload.molecular_weight_g_mol,
        )
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return GasViscosityResponse(
        mu_g_cp=result.mu_cp,
        rho_g_g_cm3=result.rho_gcc,
        molecular_weight_g_mol=result.molecular_weight_g_mol,
        z_factor=result.z_factor,
        k_factor=result.k_factor,
        x_factor=result.x_factor,
        y_factor=result.y_factor,
        in_validity_range=result.in_validity_range,
    )


@router.post(
    "/engine/reservoir/pvt/oil-rso",
    tags=["Reservoir"],
    response_model=OilRsoResponse,
    summary="Standing/Beggs solution gas-oil ratio",
)
def calculate_oil_rso(payload: OilRequest) -> OilRsoResponse:
    try:
        result = oil_solution_gor(**_oil_inputs(payload))
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return OilRsoResponse(**result.__dict__)


@router.post(
    "/engine/reservoir/pvt/oil-bo",
    tags=["Reservoir"],
    response_model=OilBoResponse,
    summary="Standing/Beggs oil formation volume factor",
)
def calculate_oil_bo(payload: OilBoRequest) -> OilBoResponse:
    try:
        result = oil_formation_volume_factor(
            **_oil_inputs(payload),
            co_psi_inv=payload.co_psi_inv,
        )
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return OilBoResponse(
        bo_bbl_stb=result.bo_bbl_stb,
        f_term=result.f_term,
        oil_specific_gravity=result.oil_specific_gravity,
        rso_scf_stb=result.rso_scf_stb,
        clamped=result.clamped,
        in_validity_range=result.in_validity_range,
        co_used_psi_inv=result.co_used_psi_inv,
    )


@router.post(
    "/engine/reservoir/pvt/oil-compressibility",
    tags=["Reservoir"],
    response_model=OilCompressibilityResponse,
    summary="Villena-Lanzi/Vasquez-Beggs oil compressibility",
)
def calculate_oil_co(payload: OilRequest) -> OilCompressibilityResponse:
    try:
        result = oil_compressibility(**_oil_inputs(payload))
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return OilCompressibilityResponse(
        co_psi_inv=result.co_psi_inv,
        formulation=result.formulation,
        rsob_scf_stb=result.rsob_scf_stb,
        in_validity_range=result.in_validity_range,
    )


@router.post(
    "/engine/reservoir/pvt/oil-viscosity",
    tags=["Reservoir"],
    response_model=OilViscosityResponse,
    summary="Egbogah/Beggs-Robinson/Vasquez-Beggs oil viscosity",
)
def calculate_oil_mu(payload: OilRequest) -> OilViscosityResponse:
    try:
        result = oil_viscosity(**_oil_inputs(payload))
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return OilViscosityResponse(
        mu_o_cp=result.mu_cp,
        mu_dead_cp=result.mu_dead_cp,
        mu_at_bubble_point_cp=result.mu_at_bubble_point_cp,
        a_factor=result.a_factor,
        b_factor=result.b_factor,
        m_exponent=result.m_exponent,
        formulation=result.formulation,
        rso_scf_stb=result.rso_scf_stb,
        in_validity_range=result.in_validity_range,
    )


@router.post(
    "/engine/reservoir/pvt/water",
    tags=["Reservoir"],
    response_model=WaterPVTResponse,
    summary="McCain/Osif formation-water PVT",
)
def calculate_water_properties(payload: WaterPVTRequest) -> WaterPVTResponse:
    try:
        result = water_pvt(
            p_psia=payload.p_psia,
            temperature_f=payload.temperature_f,
            salinity_pct=payload.salinity_pct,
            c_nacl_g_l=payload.c_nacl_g_l,
        )
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return WaterPVTResponse(
        bw_bbl_stb=result.bw_bbl_stb,
        rswp_scf_stb=result.rswp_scf_stb,
        rsw_scf_stb=result.rsw_scf_stb,
        cw_psi_inv=result.cw_psi_inv,
        mu_w_cp=result.mu_w_cp,
        bw_in_validity_range=result.bw_in_validity_range,
        rsw_in_validity_range=result.rsw_in_validity_range,
        cw_in_validity_range=result.cw_in_validity_range,
        mu_w_in_validity_range=result.mu_w_in_validity_range,
    )


def _oil_inputs(payload: OilRequest) -> dict[str, float]:
    return {
        "p_psia": payload.p_psia,
        "pb_psia": payload.pb_psia,
        "temperature_f": payload.temperature_f,
        "gas_sg": payload.gas_sg,
        "oil_api": payload.oil_api,
    }
