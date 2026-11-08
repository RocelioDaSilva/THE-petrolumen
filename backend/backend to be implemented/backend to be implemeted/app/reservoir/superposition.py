"""Superposition and image-well interference.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 7, Sec. 9, pp. 249-253, Eq. (7.57) and Fig. 7.18;
line-source solution Eq. (7.36), p. 237.
"""

from __future__ import annotations

from dataclasses import dataclass

from scipy.special import expi

# Eq. (7.36), p. 237: constants
EI_COEF = 70.6            # 70.6 q mu B / (k h)
EI_TIME_CONST = 0.00105   # phi mu ct r^2 / (0.00105 k t)

# Guard: minimum physical phi for Ei numerical stability
PHI_MIN = 1.0e-3


@dataclass(frozen=True)
class SuperpositionSource:
    q_stb_d: float        # positive = production; negative = injection
    t_start_hr: float     # when production began (> = 0)
    distance_ft: float    # source-to-observation distance (> = 0)


@dataclass(frozen=True)
class SuperpositionResult:
    dp_total_psi: float
    dp_per_source_psi: tuple[float, ...]
    ei_arguments: tuple[float, ...]
    inactive_source_indices: tuple[int, ...]


def superposition_pressure_drop(
    observation_time_hr: float,
    sources: list[SuperpositionSource],
    k_md: float,
    h_ft: float,
    mu_cp: float,
    B_bbl_stb: float,
    phi: float,
    ct_psi_inv: float,
) -> SuperpositionResult:
    """Superposed line-source pressure drop (Craft Eq. 7.36/7.57).

    Applies the principle of superposition to the line-source solution.
    Each source contributes independently:
    dp_j = (70.6 * q_j * mu * B / (k*h)) * [-Ei(-x_j)]
    with x_j = phi * mu * ct * r_j^2 / (0.00105 * k * (t - t_start_j)).

    For image wells (sealing fault), the caller adds an additional
    source at twice the fault distance. For multi-rate histories on a
    single well, the caller adds a source for each rate increment at
    the rate-change time.

    Args:
        observation_time_hr: Time of observation, hr (> 0).
        sources: List of SuperpositionSource.
        k_md: Permeability, md (> 0).
        h_ft: Net pay thickness, ft (> 0).
        mu_cp: Viscosity, cp (> 0).
        B_bbl_stb: FVF, bbl/STB (> 0).
        phi: Porosity, fraction (> PHI_MIN).
        ct_psi_inv: Total compressibility, psi^-1 (> 0).

    Returns:
        SuperpositionResult.

    Raises:
        ValueError: any input out of range, or an Ei argument computes
            non-physically.
    """
    if not (observation_time_hr > 0.0):
        raise ValueError(
            f"observation_time_hr must be > 0, got {observation_time_hr!r}"
        )
    if not (k_md > 0.0):
        raise ValueError(f"k_md must be > 0, got {k_md!r}")
    if not (h_ft > 0.0):
        raise ValueError(f"h_ft must be > 0, got {h_ft!r}")
    if not (mu_cp > 0.0):
        raise ValueError(f"mu_cp must be > 0, got {mu_cp!r}")
    if not (B_bbl_stb > 0.0):
        raise ValueError(f"B_bbl_stb must be > 0, got {B_bbl_stb!r}")
    if not (PHI_MIN <= phi < 1.0):
        raise ValueError(
            f"phi must be in [{PHI_MIN}, 1), got {phi!r}"
        )
    if not (ct_psi_inv > 0.0):
        raise ValueError(f"ct_psi_inv must be > 0, got {ct_psi_inv!r}")

    if len(sources) == 0:
        raise ValueError("sources list must be non-empty")

    for j, src in enumerate(sources):
        if not (src.t_start_hr >= 0.0):
            raise ValueError(
                f"sources[{j}].t_start_hr must be >= 0, got {src.t_start_hr!r}"
            )
        if not (src.distance_ft >= 0.0):
            raise ValueError(
                f"sources[{j}].distance_ft must be >= 0, got "
                f"{src.distance_ft!r}"
            )

    coef = EI_COEF * mu_cp * B_bbl_stb / (k_md * h_ft)
    dp_list: list[float] = []
    x_list: list[float] = []
    inactive: list[int] = []
    dp_total = 0.0

    for j, src in enumerate(sources):
        t_j = observation_time_hr - src.t_start_hr
        if t_j <= 0.0:
            dp_list.append(0.0)
            x_list.append(float("nan"))
            inactive.append(j)
            continue

        if src.distance_ft == 0.0:
            # Cannot evaluate Ei at zero; treat as immediate full
            # drawdown (well at observation point). Mathematically
            # singular; caller should not pass r=0.
            raise ValueError(
                f"sources[{j}].distance_ft must be > 0 for observation "
                "at a distinct point (r=0 is singular in Ei)"
            )

        x = (
            phi * mu_cp * ct_psi_inv * src.distance_ft * src.distance_ft
            / (EI_TIME_CONST * k_md * t_j)
        )
        if not (x > 0.0):
            raise ValueError(
                f"sources[{j}]: Ei argument x = {x!r} <= 0; check inputs."
            )
        # -Ei(-x) = -expi(-x), positive for x > 0
        neg_ei = -float(expi(-x))
        dp_j = coef * src.q_stb_d * neg_ei
        dp_list.append(dp_j)
        x_list.append(x)
        dp_total += dp_j

    return SuperpositionResult(
        dp_total_psi=dp_total,
        dp_per_source_psi=tuple(dp_list),
        ei_arguments=tuple(x_list),
        inactive_source_indices=tuple(inactive),
    )
