from pydantic import BaseModel, Field

class CompactionRequest(BaseModel):
    phi_baseline: float = Field(..., gt=0.0, lt=1.0)
    a_per_psi: float
    p_psia: float = Field(..., gt=0.0)

class CompactionResponse(BaseModel):
    phi_actual: float = Field(..., gt=0.0)
    delta_phi: float
    compaction_compressibility_per_psi: float
