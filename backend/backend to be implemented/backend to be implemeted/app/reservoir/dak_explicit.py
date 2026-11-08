"""Explicit DAK Z-factor with visible constants (Craft ref. 14, p. 17)."""
from __future__ import annotations
from dataclasses import dataclass
import math

A1, A2, A3 = 0.3265, -1.0700, -0.5339
A4, A5, A6 = 0.01569, -0.05165, 0.5475
A7, A8 = -0.7361, 0.1844


@dataclass(frozen=True)
class DAKResult:
    Z: float
    rho_r: float
    n_iter: int
    residual: float
    converged: bool


def dak_z_factor(pr: float, Tr: float,
                 tol: float = 1e-8, max_iter: int = 50) -> DAKResult:
    """DAK Z-factor via successive substitution.

    Args:
        pr: Reduced pressure (> 0).
        Tr: Reduced temperature (> 0).
        tol: Convergence tolerance on Z.
        max_iter: Max iterations.

    Returns:
        DAKResult.

    Raises:
        ValueError: pr or Tr out of range, or non-convergence.
    """
    if not (pr > 0.0):
        raise ValueError(f"pr must be > 0, got {pr!r}")
    if not (Tr > 0.0):
        raise ValueError(f"Tr must be > 0, got {Tr!r}")
    if tol <= 0.0:
        raise ValueError(f"tol must be > 0, got {tol!r}")
    rho = 0.27 * pr / Tr      # Z=1 initial guess
    Z = 1.0
    for n in range(1, max_iter + 1):
        Tr2 = Tr * Tr
        Tr3 = Tr2 * Tr
        Z_rhs = (1.0
                 + (A1 + A2 / Tr + A3 / Tr3) * rho
                 + (A4 + A5 / Tr) * rho ** 2
                 + (A5 * A6 / Tr) * rho ** 5
                 + (A7 / Tr3) * rho ** 2 * (1.0 + A8 * rho ** 2)
                   * math.exp(-A8 * rho ** 2))
        Z_new = Z_rhs
        rho_new = 0.27 * pr / (Z_new * Tr)
        resid = abs(Z_new - Z)
        if resid < tol:
            return DAKResult(Z=Z_new, rho_r=rho_new, n_iter=n,
                             residual=resid, converged=True)
        Z = Z_new
        rho = rho_new
    raise ValueError(
        f"DAK did not converge in {max_iter} iters: "
        f"pr={pr}, Tr={Tr}, residual={resid:.3e}"
    )
