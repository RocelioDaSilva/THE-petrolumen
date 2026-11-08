"""Gas displacement with gravity segregation.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 9, Sec. 3.2, pp. 354-360, Eqs. (9.18)-(9.26),
Table 9.2, Fig. 9.13, worked example on p. 357.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

GRAV_COEF = 7.821e-6      # Eq. (9.23), p. 356
BBL_PER_CUFT = 5.615      # Eq. (9.26), p. 358


@dataclass(frozen=True)
class GasGravityResult:
    f_g: float
    lambda_gravity: float
    denom_visc: float
    counter_current: bool


@dataclass(frozen=True)
class GasFrontPoint:
    Sg: float
    fg: float
    dfg_dSg: float


def _validate_common(
    mu_o: float, mu_g: float, k_md: float, Ac_ft2: float,
    qt_bbl_d: float, alpha_deg: float, phi: float,
) -> None:
    if not (mu_o > 0.0):
        raise ValueError(f"mu_o must be > 0, got {mu_o!r}")
    if not (mu_g > 0.0):
        raise ValueError(f"mu_g must be > 0, got {mu_g!r}")
    if not (k_md > 0.0):
        raise ValueError(f"k_md must be > 0, got {k_md!r}")
    if not (Ac_ft2 > 0.0):
        raise ValueError(f"Ac_ft2 must be > 0, got {Ac_ft2!r}")
    if not (qt_bbl_d > 0.0):
        raise ValueError(f"qt_bbl_d must be > 0, got {qt_bbl_d!r}")
    if not (-90.0 < alpha_deg < 90.0):
        raise ValueError(
            f"alpha_deg must be in (-90, 90), got {alpha_deg!r}"
        )
    if not (0.0 < phi < 1.0):
        raise ValueError(f"phi must be in (0, 1), got {phi!r}")


def gas_fractional_flow_gravity(
    Sg: float,
    So: float,
    k_ro: float,
    k_rg: float,
    mu_o: float,
    mu_g: float,
    k_md: float,
    Ac_ft2: float,
    qt_bbl_d: float,
    alpha_deg: float,
    rho_o_lb_ft3: float,
    rho_g_lb_ft3: float,
) -> GasGravityResult:
    """Fractional gas flow with gravity (Eq. 9.23, p. 356).

    Computes fg = (1 - lambda*kro) / (1 + kro*mu_g/(krg*mu_o))
    with lambda = 7.821e-6 * k * (rho_o - rho_g) * cos(alpha) /
    (mu_o * v_t) and v_t = qt/Ac.

    Args:
        Sg: Gas saturation, fraction [0, 1).
        So: Oil saturation, fraction (0, 1].
        k_ro: Oil relative permeability (>= 0).
        k_rg: Gas relative permeability (>= 0; must be > 0 if Sg > 0).
        mu_o: Oil viscosity, cp (> 0).
        mu_g: Gas viscosity, cp (> 0).
        k_md: Absolute permeability, md (> 0).
        Ac_ft2: Cross-sectional area, ft^2 (> 0).
        qt_bbl_d: Total reservoir-barrel rate, bbl/day (> 0).
        alpha_deg: Dip angle from horizontal, degrees (-90, 90).
        rho_o_lb_ft3: Oil density, lb/cu-ft (> 0).
        rho_g_lb_ft3: Gas density, lb/cu-ft (> 0; < rho_o).

    Returns:
        GasGravityResult.

    Raises:
        ValueError: any input out of range, or k_rg = 0 with Sg > 0.
    """
    if not (0.0 <= Sg < 1.0):
        raise ValueError(f"Sg must be in [0, 1), got {Sg!r}")
    if not (0.0 < So <= 1.0):
        raise ValueError(f"So must be in (0, 1], got {So!r}")
    if not (k_ro >= 0.0):
        raise ValueError(f"k_ro must be >= 0, got {k_ro!r}")
    if not (k_rg >= 0.0):
        raise ValueError(f"k_rg must be >= 0, got {k_rg!r}")
    if Sg > 0.0 and not (k_rg > 0.0):
        raise ValueError(
            f"k_rg must be > 0 when Sg > 0; got k_rg={k_rg!r}, Sg={Sg!r}"
        )
    _validate_common(mu_o, mu_g, k_md, Ac_ft2, qt_bbl_d, alpha_deg, 0.5)
    if not (rho_o_lb_ft3 > 0.0):
        raise ValueError(f"rho_o must be > 0, got {rho_o_lb_ft3!r}")
    if not (rho_g_lb_ft3 >= 0.0):
        raise ValueError(f"rho_g must be >= 0, got {rho_g_lb_ft3!r}")
    if not (rho_o_lb_ft3 > rho_g_lb_ft3):
        raise ValueError(
            f"rho_o ({rho_o_lb_ft3!r}) must exceed rho_g "
            f"({rho_g_lb_ft3!r})"
        )

    v_t = qt_bbl_d / Ac_ft2
    cos_a = math.cos(math.radians(alpha_deg))
    lambda_grav = (
        GRAV_COEF * k_md * (rho_o_lb_ft3 - rho_g_lb_ft3) * cos_a
        / (mu_o * v_t)
    )

    num = 1.0 - lambda_grav * k_ro
    if k_rg > 0.0:
        visc_term = (k_ro / k_rg) * (mu_g / mu_o)
    else:
        # Sg=0 exactly: krg=0 => no gas phase, fg=0
        return GasGravityResult(
            f_g=0.0, lambda_gravity=lambda_grav,
            denom_visc=float("inf"), counter_current=False,
        )
    denom = 1.0 + visc_term
    if not (denom > 0.0):
        raise ValueError(
            f"fg denominator = {denom!r} <= 0; check k_ro, k_rg, "
            "mu_o, mu_g."
        )
    fg = num / denom
    return GasGravityResult(
        f_g=fg, lambda_gravity=lambda_grav,
        denom_visc=denom, counter_current=(fg < 0.0),
    )


def gas_gravity_frontal_advance(
    Sg_list: list[float],
    fg_list: list[float],
    qi_bbl_d: float,
    phi: float,
    Ac_ft2: float,
    times_days: list[float],
) -> tuple[tuple[tuple[float, ...], ...], tuple[float, ...]]:
    """Front positions x(Sg, t) from precomputed fg(Sg) (Eq. 9.26).

    This helper assumes the caller has already computed fg at each Sg
    (e.g., via gas_fractional_flow_gravity) and just needs the
    frontal-advance multiplication. dfg/dSg is computed by finite
    difference from the supplied (Sg, fg) pairs.

    Args:
        Sg_list: Saturation values (sorted ascending, each in [0, 1)).
        fg_list: Corresponding fg values (same length).
        qi_bbl_d: Total reservoir-barrel rate, bbl/day (> 0).
        phi: Porosity, fraction (0, 1).
        Ac_ft2: Cross-sectional area, ft^2 (> 0).
        times_days: Observation times (each >= 0).

    Returns:
        (x_by_Sg_by_time, times_days_tuple).

    Raises:
        ValueError: malformed inputs.
    """
    if len(Sg_list) != len(fg_list):
        raise ValueError("Sg_list and fg_list must have same length")
    if len(Sg_list) < 3:
        raise ValueError("at least 3 Sg points required for dfg/dSg")
    for i in range(1, len(Sg_list)):
        if not (Sg_list[i] > Sg_list[i - 1]):
            raise ValueError(
                f"Sg_list must be strictly increasing; index {i} "
                f"violated ({Sg_list[i-1]} -> {Sg_list[i]})"
            )
    if not (qi_bbl_d > 0.0):
        raise ValueError(f"qi_bbl_d must be > 0, got {qi_bbl_d!r}")
    if not (0.0 < phi < 1.0):
        raise ValueError(f"phi must be in (0, 1), got {phi!r}")
    if not (Ac_ft2 > 0.0):
        raise ValueError(f"Ac_ft2 must be > 0, got {Ac_ft2!r}")
    for i, t in enumerate(times_days):
        if not (t >= 0.0):
            raise ValueError(f"times_days[{i}] must be >= 0, got {t!r}")

    coef = BBL_PER_CUFT * qi_bbl_d / (phi * Ac_ft2)
    n = len(Sg_list)
    dfg = [0.0] * n
    # Central differences in interior; forward/backward at ends
    for i in range(n):
        if i == 0:
            dfg[i] = (fg_list[1] - fg_list[0]) / (Sg_list[1] - Sg_list[0])
        elif i == n - 1:
            dfg[i] = (fg_list[-1] - fg_list[-2]) / (Sg_list[-1] - Sg_list[-2])
        else:
            dfg[i] = (fg_list[i+1] - fg_list[i-1]) / (Sg_list[i+1] - Sg_list[i-1])

    rows: list[tuple[float, ...]] = []
    for i in range(n):
        row = tuple(coef * t * dfg[i] for t in times_days)
        rows.append(row)
    return tuple(rows), tuple(times_days)
