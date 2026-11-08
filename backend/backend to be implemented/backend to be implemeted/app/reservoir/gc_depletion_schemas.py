"""Pydantic v2 schemas for the gas-condensate depletion endpoint."""

from pydantic import BaseModel, Field, model_validator


class GCDepletionIncrement(BaseModel):
    p_end_psia: float = Field(..., gt=0.0)
    V_produced_cc: float = Field(..., gt=0.0)
    z: float = Field(..., gt=0.0)
    comp: dict[str, float] = Field(
        ..., description="Mole fractions: C4, C5, C6, C7plus"
    )


class GCDepletionRequest(BaseModel):
    pi_psia: float = Field(..., gt=0.0)
    T_F: float = Field(..., gt=-459.67)
    phi_frac: float = Field(..., gt=0.0, lt=1.0)
    Swi_frac: float = Field(..., ge=0.0, lt=1.0)
    z_initial: float = Field(..., gt=0.0)
    cell_volume_cc: float = Field(..., gt=0.0)
    increments: list[GCDepletionIncrement] = Field(..., min_length=1)
    initial_comp: dict[str, float]
    mw_per_comp: dict[str, float]
    sg_per_comp: dict[str, float]
    rec_C4: float = Field(0.25, ge=0.0, le=1.0)
    rec_C5: float = Field(0.50, ge=0.0, le=1.0)
    rec_C6: float = Field(0.75, ge=0.0, le=1.0)
    rec_C7plus: float = Field(1.00, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _check_monotone(self) -> "GCDepletionRequest":
        prev = None
        for i, inc in enumerate(self.increments):
            if prev is not None and inc.p_end_psia >= prev:
                raise ValueError(
                    f"increments[{i}] pressure not strictly decreasing"
                )
            prev = inc.p_end_psia
        return self


class GCDepletionRow(BaseModel):
    p_end_psia: float
    dV_reservoir_cuft_per_acft: float
    dGp_mmscf_per_acft: float
    dResidue_mmscf_per_acft: float
    dLiquid_bbl_per_acft: float
    gor_scf_per_bbl: float
    cum_Gp_mmscf_per_acft: float
    cum_residue_mmscf_per_acft: float
    cum_liquid_bbl_per_acft: float
    gross_gas_recovery_pct: float
    residue_recovery_pct: float
    liquid_recovery_pct: float


class GCDepletionResponse(BaseModel):
    g_initial_mmscf_per_acft: float = Field(..., gt=0.0)
    liquid_initial_bbl_per_acft: float = Field(..., ge=0.0)
    rows: list[GCDepletionRow]
    late_time_zero_liquid: bool
