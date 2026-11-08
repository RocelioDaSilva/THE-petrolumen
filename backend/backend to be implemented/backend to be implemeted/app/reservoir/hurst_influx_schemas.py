from pydantic import BaseModel, Field, model_validator


class HurstPoint(BaseModel):
    t_days: float = Field(..., ge=0.0)
    p_psia: float = Field(..., gt=0.0)


class HurstRequest(BaseModel):
    c_prime: float = Field(..., gt=0.0)
    a_per_day: float = Field(..., gt=0.0)
    pi_psia: float = Field(..., gt=0.0)
    p_history: list[HurstPoint] = Field(..., min_length=2)

    @model_validator(mode="after")
    def _mono(self):
        for i in range(1, len(self.p_history)):
            if self.p_history[i].t_days <= self.p_history[i-1].t_days:
                raise ValueError("p_history times must strictly increase")
        return self


class HurstResponse(BaseModel):
    we_cumulative_bbl: float
    we_at_points_bbl: list[float]
