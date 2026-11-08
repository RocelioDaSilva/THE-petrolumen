from pydantic import BaseModel, Field


class TwoPhaseFVFRequest(BaseModel):
    Bo_bbl_stb: float = Field(..., gt=0.0)
    Bg_bbl_scf: float = Field(..., gt=0.0)
    Rsoi_scf_stb: float = Field(..., ge=0.0)
    Rso_scf_stb: float = Field(..., ge=0.0)


class TwoPhaseFVFResponse(BaseModel):
    Bt_bbl_stb: float
    free_gas_term_bbl_stb: float
    Rso_gt_Rsoi: bool
