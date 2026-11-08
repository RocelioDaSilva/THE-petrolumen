"""Stratigraphic transmissibility for dipping layers.

Source: Chin, W.C. (2016), Reservoir Engineering in Modern Oilfields,
Wiley, Ch. 2, Eq. (2-38) and Eq. (2-44), pp. 45-47.
"""
from __future__ import annotations
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class StratTransResult:
    TX: np.ndarray
    TY: np.ndarray
    TZ: np.ndarray
    hz_min: float
    hz_max: float


def stratigraphic_transmissibility(
    Z_m: np.ndarray, k_md: np.ndarray,
    dx_m: float, dy_m: float,
) -> StratTransResult:
    """Stratigraphic (dipping-layer) transmissibilities, Chin Eq. (2-44).

    Args:
        Z_m: Grid heights, shape (n_i, n_j, n_k+1), all finite.
        k_md: Layer permeabilities, shape (n_i, n_j, n_k), all > 0.
        dx_m, dy_m: Grid spacing, > 0.

    Returns:
        StratTransResult with TX, TY, TZ arrays and layer-thickness range.

    Raises:
        ValueError: shape mismatch, non-positive dx/dy, k <= 0,
            or any h_z <= 0 (pinch-out).
    """
    Z = np.asarray(Z_m, dtype=float)
    k = np.asarray(k_md, dtype=float)
    if Z.ndim != 3 or k.ndim != 3:
        raise ValueError("Z and k must be 3D arrays")
    if Z.shape[:2] != k.shape[:2]:
        raise ValueError(
            f"Z and k must share first two dims, got "
            f"{Z.shape[:2]} vs {k.shape[:2]}"
        )
    if Z.shape[2] != k.shape[2] + 1:
        raise ValueError(
            f"Z third dim must be k third dim + 1, got {Z.shape[2]} "
            f"vs {k.shape[2]}"
        )
    if not (dx_m > 0.0 and dy_m > 0.0):
        raise ValueError(
            f"dx_m, dy_m must be > 0, got {dx_m!r}, {dy_m!r}"
        )
    if np.any(k <= 0.0):
        raise ValueError("all k_md must be > 0")
    hz = Z[:, :, 1:] - Z[:, :, :-1]
    if np.any(hz <= 0.0):
        raise ValueError("layer thickness h_z <= 0 found (pinch-out)")

    TX = np.zeros_like(k)
    TY = np.zeros_like(k)
    TZ = np.zeros_like(k)
    ni, nj, nk = k.shape

    for i in range(ni - 1):
        num = 2.0 * k[i, :, :] * k[i + 1, :, :]
        den = k[i, :, :] + k[i + 1, :, :]
        TX[i, :, :] = (dy_m * hz[i, :, :] / dx_m) * num / den

    for j in range(nj - 1):
        num = 2.0 * k[:, j, :] * k[:, j + 1, :]
        den = k[:, j, :] + k[:, j + 1, :]
        TY[:, j, :] = (dx_m * hz[:, j, :] / dy_m) * num / den

    for m in range(nk - 1):
        num = 2.0 * k[:, :, m] * k[:, :, m + 1]
        den = k[:, :, m] + k[:, :, m + 1]
        TZ[:, :, m] = (dx_m * dy_m / hz[:, :, m]) * num / den

    return StratTransResult(
        TX=TX, TY=TY, TZ=TZ,
        hz_min=float(np.min(hz)), hz_max=float(np.max(hz)),
    )
