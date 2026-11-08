from pydantic import BaseModel, Field, model_validator


class StorageSplitRequest(BaseModel):
    G_scf: float = Field(..., gt=0.0)
    pi_over_zi: float = Field(..., gt=0.0)
    base_pz: float = Field(..., gt=0.0)
    max_pz: float = Field(..., gt=0.0)

    @model_validator(mode="after")
    def _chk(self):
        if self.base_pz >= self.max_pz:
            raise ValueError("base_pz must be < max_pz")
        return self


class StorageSplitResponse(BaseModel):
    base_gas_scf: float
    working_gas_scf: float
    max_gas_scf: float
    unused_gas_scf: float
    base_fraction: float
    working_fraction: float
