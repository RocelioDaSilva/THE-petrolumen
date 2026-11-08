from pydantic import BaseModel, Field, model_validator


class GasMBWeRequest(BaseModel):
    Vb_cuft: float = Field(..., gt=0.0)
    phi: float = Field(..., gt=0.0, lt=1.0)
    Swi: float = Field(..., ge=0.0, lt=1.0)
    Bgi: float = Field(..., gt=0.0)
    Bgf: float = Field(..., gt=0.0)
    Gp_scf: float = Field(..., ge=0.0)
    Wp_bbl: float = Field(..., ge=0.0)
    Bw: float = Field(..., gt=0.0)
    Vb_invaded_cuft: float = Field(..., gt=0.0)

    @model_validator(mode="after")
    def _chk(self):
        if self.Bgf <= self.Bgi:
            raise ValueError("Bgf must exceed Bgi")
        return self


class GasMBWeResponse(BaseModel):
    G_scf: float
    We_cuft: float
    Sw_invaded: float
    Sgr_invaded: float
    out_of_physical_range: bool
