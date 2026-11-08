from pydantic import BaseModel, Field, model_validator


class DamageSkinRequest(BaseModel):
    k_e_md: float = Field(..., gt=0.0)
    k_a_md: float = Field(..., gt=0.0)
    r_a_ft: float = Field(..., gt=0.0)
    r_w_ft: float = Field(..., gt=0.0)

    @model_validator(mode="after")
    def _chk(self):
        if self.r_a_ft <= self.r_w_ft:
            raise ValueError("r_a_ft must exceed r_w_ft")
        return self


class DamageSkinResponse(BaseModel):
    S: float
    kind: str
