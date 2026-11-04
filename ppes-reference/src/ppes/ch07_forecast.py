"""Chapter 7 â€” Forecast of Well Production (pp. 7/87 â€“ 7/95)."""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np


@dataclass
class ForecastStep:
    pressure: float
    rate: float
    cum_prod: float
    time_days: float


@dataclass
class ForecastResult:
    steps: list[ForecastStep] = field(default_factory=list)

    def to_table(self):
        import pandas as pd
        return pd.DataFrame([s.__dict__ for s in self.steps])


@dataclass
class PVTTable:
    pressures: np.ndarray
    Rs: np.ndarray
    Bo: np.ndarray
    Bg: np.ndarray
    mu_o: np.ndarray
    kro: np.ndarray
    krg: np.ndarray

    def interp(self, p: float) -> dict:
        return {
            "Rs":  float(np.interp(p, self.pressures, self.Rs)),
            "Bo":  float(np.interp(p, self.pressures, self.Bo)),
            "Bg":  float(np.interp(p, self.pressures, self.Bg)),
            "mu_o": float(np.interp(p, self.pressures, self.mu_o)),
            "kro": float(np.interp(p, self.pressures, self.kro)),
            "krg": float(np.interp(p, self.pressures, self.krg)),
        }


def transient_forecast_oil(*args, **kwargs):
    """Transient oil forecast â€” Sect. 7.2, Eq. 7.1.

    TODO: sequence of transient nodal analyses at each month.
    Validate against Example 7.1 (Table 7.1).
    """
    raise NotImplementedError("Implement per Sect. 7.2, Eq. 7.1.")


def pseudo_steady_1phase_oil(*args, **kwargs):
    """1-phase pseudo-steady forecast â€” Sect. 7.3.1, Eqs. 7.2â€“7.7."""
    raise NotImplementedError("Implement per Sect. 7.3.1, Eqs. 7.2â€“7.7.")


def tarver_two_phase(*args, **kwargs):
    """Two-phase material balance â€” Sect. 7.3.2, Eqs. 7.9â€“7.14.

    TODO: iterate on R until convergence at each pressure step. Validate
    against Example 7.3 (Tables 7.3â€“7.5).
    """
    raise NotImplementedError("Implement per Sect. 7.3.2, Eqs. 7.9â€“7.14.")