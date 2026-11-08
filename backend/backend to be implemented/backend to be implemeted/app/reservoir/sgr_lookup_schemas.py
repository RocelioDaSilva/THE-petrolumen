from pydantic import BaseModel, Field


class SgrLookupRequest(BaseModel):
    rock_name: str = Field(..., min_length=1)


class SgrLookupResponse(BaseModel):
    Sgr: float
    Sgr_pct: float
    used_table_average: bool
    rock_name_resolved: str
