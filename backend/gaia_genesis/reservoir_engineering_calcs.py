import numpy as np
from typing import Dict, Any


def calculate_ogip_volumetric(
    area: float, thickness: float, porosity: float, sw: float, bg: float
) -> float:
    """
    Volumetric OGIP = 43560 * A * h * phi * (1 - Sw) / Bg (scf)
    area in acres, thickness in ft, bg in res ft3 / scf
    """
    return 43560 * area * thickness * porosity * (1 - sw) / bg


def calculate_stoiip_volumetric(
    area: float, thickness: float, porosity: float, sw: float, bo: float
) -> float:
    """
    Volumetric STOIIP = 7758 * A * h * phi * (1 - Sw) / Bo (stb)
    area in acres, thickness in ft
    """
    return 7758 * area * thickness * porosity * (1 - sw) / bo


def havlena_odeh_oil(
    Np: np.ndarray,
    Bo: np.ndarray,
    Rs: np.ndarray,
    Rsi: float,
    Bg: np.ndarray,
    Boi: float,
) -> Dict[str, Any]:
    """
    Havlena-Odeh for under-saturated oil reservoir: F = N * Eo
    F = Np * Bo
    Eo = (Bo - Boi)
    Returns OOIP (N) from slope of F vs Eo passing through origin.
    """
    F = Np * Bo
    Eo = Bo - Boi
    # Fit y = m*x (no intercept)
    m = np.sum(F * Eo) / np.sum(Eo**2)
    return {"ooip": float(m), "data": {"F": F.tolist(), "Eo": Eo.tolist()}}


def pz_analysis(pressure: np.ndarray, z: np.ndarray, Gp: np.ndarray) -> Dict[str, Any]:
    """
    P/Z vs Gp Analysis.
    Intercept at Gp=0 is Pi/Zi. Intercept at P/Z=0 is OGIP.
    """
    pz = pressure / z
    slope, intercept = np.polyfit(Gp, pz, 1)
    ogip = -intercept / slope if slope != 0 else 0
    return {
        "ogip": float(ogip),
        "pi_zi": float(intercept),
        "slope": float(slope),
        "data": {"Gp": Gp.tolist(), "pz": pz.tolist()},
    }
