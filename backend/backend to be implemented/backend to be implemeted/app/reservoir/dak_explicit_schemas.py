from pydantic import BaseModel, Field

class DAKRequest(BaseModel):
    pr: float = Field(..., gt=0.0)
    Tr: float = Field(..., gt=0.0)
    tol: float = Field(1e-8, gt=0.0)
    max_iter: int = Field(50, ge=1, le=500)

class DAKResponse(BaseModel):
    Z: float
    rho_r: float
    n_iter: int
    residual: float
    converged: bool
