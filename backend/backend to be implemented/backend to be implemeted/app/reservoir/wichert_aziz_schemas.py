from pydantic import BaseModel, Field, model_validator


class WichertAzizRequest(BaseModel):
    y_H2S: float = Field(..., ge=0.0, lt=1.0)
    y_CO2: float = Field(..., ge=0.0, lt=1.0)
    Tpc_R: float = Field(..., gt=0.0)
    ppc_psia: float = Field(..., gt=0.0)

    @model_validator(mode="after")
    def _chk(self):
        if self.y_H2S + self.y_CO2 >= 1.0:
            raise ValueError("y_H2S + y_CO2 must be < 1")
        return self


class WichertAzizResponse(BaseModel):
    Tpc_adj_R: float
    ppc_adj_psia: float
    epsilon_R: float
    A_total: float
