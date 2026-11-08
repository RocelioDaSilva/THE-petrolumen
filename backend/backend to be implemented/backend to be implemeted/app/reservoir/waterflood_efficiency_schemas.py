"""Pydantic v2 schemas for the waterflood-efficiency endpoint."""

from typing import Literal
from pydantic import BaseModel, Field, model_validator


class WaterfloodEffRequest(BaseModel):
    mode: Literal["from_components", "from_saturations"]
    E_a: float | None = Field(default=None, ge=0.0, le=1.0)
    E_i: float | None = Field(default=None, ge=0.0, le=1.0)
    E_d: float | None = Field(default=None, ge=0.0, le=1.0)
    Swr: float | None = Field(default=None, gt=0.0, lt=1.0)
    Sor: float | None = Field(default=None, ge=0.0)

    @model_validator(mode="after")
    def _check(self) -> "WaterfloodEffRequest":
        if self.mode == "from_components":
            for name in ("E_a", "E_i", "E_d"):
                if getattr(self, name) is None:
                    raise ValueError(
                        f"{name} required for from_components mode"
                    )
        else:
            for name in ("Swr", "Sor", "E_a", "E_i"):
                if getattr(self, name) is None:
                    raise ValueError(
                        f"{name} required for from_saturations mode"
                    )
            if self.Swr is not None and self.Sor is not None:
                if self.Swr + self.Sor >= 1.0:
                    raise ValueError("Swr + Sor must be < 1")
        return self


class WaterfloodEffResponse(BaseModel):
    E_a: float | None
    E_i: float | None
    E_d: float | None
    E_v: float = Field(..., ge=0.0, le=1.0)
    E: float = Field(..., ge=0.0, le=1.0)
