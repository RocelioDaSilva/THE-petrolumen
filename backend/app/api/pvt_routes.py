"""HTTP routes for material balance (MBAL) reservoir and PVT calculations."""

from __future__ import annotations

import math
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import Field, model_validator

from .base import APIModel as BaseModel

from ..engines.pvt.mbal import MaterialBalance

router = APIRouter()


class ProductionPointInput(BaseModel):
    oil_prod: float | None = Field(
        default=None,
        ge=0.0,
        example=500000.0,
        description="Oil production volume in STB.",
    )
    gas_prod: float | None = Field(
        default=None,
        ge=0.0,
        example=5000000.0,
        description="Gas production volume in Mscf.",
    )
    water_prod: float | None = Field(
        default=None,
        ge=0.0,
        example=100.0,
        description="Water production volume in STB.",
    )


class PvtPointInput(BaseModel):
    pressure: float = Field(
        ...,
        gt=0.0,
        example=3200.0,
        description="Pressure in psia.",
    )
    bo: float | None = Field(
        default=None,
        gt=0.0,
        example=1.0,
        description="Oil formation volume factor (res bbl/STB).",
    )
    bg: float | None = Field(
        default=None,
        gt=0.0,
        example=0.0011,
        description="Gas formation volume factor.",
    )
    rs: float | None = Field(
        default=None,
        ge=0.0,
        example=0.0,
        description="Solution gas-oil ratio (scf/STB).",
    )
    rv: float | None = Field(
        default=None,
        ge=0.0,
        example=0.0,
        description="Volatile oil-gas ratio.",
    )
    z: float | None = Field(
        default=None,
        gt=0.0,
        example=0.84,
        description="Gas Z-factor.",
    )


class MbalRequest(BaseModel):
    reservoir_type: Literal["oil", "gas"] = Field(
        default="oil",
        example="gas",
        description="Reservoir fluid type: 'oil' or 'gas'.",
    )
    pressure_history: list[float] = Field(
        ...,
        min_length=2,
        example=[4000.0, 3200.0],
        description="Pressure history points in psia (at least 2 required).",
    )
    production_history: list[ProductionPointInput] = Field(
        ...,
        min_length=1,
        example=[{"oil_prod": 0.0, "gas_prod": 5000000.0, "water_prod": 100.0}],
        description="Historical production records.",
    )
    pvt_data: list[PvtPointInput] | None = Field(
        default=None,
        example=[
            {"pressure": 3200.0, "bo": 1.0, "bg": 0.0011, "rs": 0.0, "z": 0.84},
            {"pressure": 4000.0, "bo": 1.0, "bg": 0.00082, "rs": 0.0, "z": 0.89},
        ],
        description="PVT table points. If omitted, default gas/oil PVT values are interpolated.",
    )
    m: float = Field(
        default=0.0,
        ge=0.0,
        example=0.0,
        description="Gas-cap ratio m (dimensionless).",
    )
    We: float = Field(
        default=500.0,
        ge=0.0,
        example=500.0,
        description="Cumulative water influx We in STB.",
    )
    Wp: float = Field(
        default=100.0,
        ge=0.0,
        example=100.0,
        description="Cumulative water production Wp in STB.",
    )
    Gp: float = Field(
        default=0.0,
        ge=0.0,
        example=0.0,
        description="Cumulative gas production Gp in Mscf.",
    )
    Bw: float = Field(
        default=1.0,
        gt=0.0,
        example=1.0,
        description="Water formation volume factor Bw.",
    )
    cw: float = Field(
        default=3e-6,
        ge=0.0,
        example=3e-6,
        description="Water compressibility cw in 1/psi.",
    )
    cf: float = Field(
        default=3e-6,
        ge=0.0,
        example=3e-6,
        description="Formation compressibility cf in 1/psi.",
    )
    Swi: float = Field(
        default=0.2,
        ge=0.0,
        lt=1.0,
        example=0.2,
        description="Initial connate water saturation fraction (0 <= Swi < 1).",
    )

    @model_validator(mode="after")
    def validate_finite_inputs(self) -> "MbalRequest":
        for p in self.pressure_history:
            if not math.isfinite(p) or p <= 0:
                raise ValueError("Pressure history values must be positive finite numbers.")
        for val in (self.m, self.We, self.Wp, self.Gp, self.Bw, self.cw, self.cf, self.Swi):
            if not math.isfinite(val):
                raise ValueError("Scalar parameters must be finite numbers.")
        return self


class MbalResponse(BaseModel):
    reservoir_type: str
    ooip_or_ogip: float = Field(
        ...,
        description="Estimated OOIP (STB for oil) or OGIP (Mscf for gas).",
    )
    drive_indices: dict[str, float] | None = Field(
        default=None,
        description="Drive indices breakdown if available, else null.",
    )
    note: str = Field(
        ...,
        description="Operational context or limitation note regarding material balance solution.",
    )


@router.post(
    "/engine/pvt/mbal",
    tags=["PVT"],
    response_model=MbalResponse,
)
def calculate_material_balance(payload: MbalRequest) -> MbalResponse:
    """Calculate material balance for oil or gas reservoir using Havlena-Odeh solver."""
    mbal = MaterialBalance(reservoir_type=payload.reservoir_type)

    for p in payload.pressure_history:
        mbal.add_pressure_point(p)

    for prod in payload.production_history:
        mbal.add_production_point(
            oil_prod=prod.oil_prod,
            gas_prod=prod.gas_prod,
            water_prod=prod.water_prod,
        )

    if payload.pvt_data:
        for pvt in payload.pvt_data:
            mbal.add_pvt_data(
                pressure=pvt.pressure,
                bo=pvt.bo,
                bg=pvt.bg,
                rs=pvt.rs,
                rv=pvt.rv,
                z=pvt.z,
            )
    else:
        # Default PVT table across pressure range
        p_min = min(payload.pressure_history)
        p_max = max(payload.pressure_history)
        mbal.add_pvt_data(p_min, bo=1.2, bg=0.0011, rs=400.0, z=0.84)
        mbal.add_pvt_data(p_max, bo=1.25, bg=0.00082, rs=500.0, z=0.89)

    try:
        if payload.reservoir_type == "oil":
            result = mbal.solve_oil_mbal(
                m=payload.m,
                We=payload.We,
                Wp=payload.Wp,
                Gp=payload.Gp,
                Bw=payload.Bw,
                cw=payload.cw,
                cf=payload.cf,
                Swi=payload.Swi,
            )
        else:
            result = mbal.solve_gas_mbal(
                We=payload.We,
                Wp=payload.Wp,
                Bw=payload.Bw,
                cw=payload.cw,
                cf=payload.cf,
                Swi=payload.Swi,
            )
    except (ValueError, KeyError, ArithmeticError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    scalar_result = float(result)

    return MbalResponse(
        reservoir_type=payload.reservoir_type,
        ooip_or_ogip=scalar_result,
        drive_indices=None,
        note="drive indices not computed — mbal.py returns scalar only",
    )
