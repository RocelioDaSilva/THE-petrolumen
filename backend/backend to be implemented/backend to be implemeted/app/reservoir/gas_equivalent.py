"""Gas equivalent of condensate and water.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 3, Sec. 6, pp. 91-95, Eqs. (3.21)-(3.24)
and the water-equivalent value on p. 92.
"""

from __future__ import annotations

from dataclasses import dataclass

# Eq. (3.21), p. 92: combined constant
GE_COEFF = 133_000.0        # SCF/bbl

# Eq. (3.22), p. 92: Mw from API (preferred form for this engine)
MW_NUM = 5954.0
MW_API_OFFSET = 8.811

# Eq. (3.22), p. 92: Mw from gamma_o (alternative form)
MW_GAMMA_NUM = 42.43
MW_GAMMA_DEN_OFFSET = 1.008

# Eq. (4.2) / p. 111: API to specific gravity (used internally only
# when caller supplies oil_api without gamma_o)
API_TO_SG_NUM = 141.5
API_TO_SG_DEN_OFFSET = 131.5

# Water gas equivalent (book p. 92)
GE_WATER = 7390.0           # SCF/surface bbl (fresh water reference)


@dataclass(frozen=True)
class GasEquivalentResult:
    ge_scf_per_bbl: float
    ge_water_scf_per_bbl: float
    gp_total_scf: float
    gw_total_scf: float
    gamma_o: float
    mw_o: float
    in_validity: bool


def gas_equivalent(
    Np_stb: float,
    gamma_o: float | None = None,
    M_wo: float | None = None,
    oil_api: float | None = None,
    Wp_water_bbl: float = 0.0,
    Gp_surf_scf: float = 0.0,
) -> GasEquivalentResult:
    """Convert condensate and water to gas-equivalent volumes.

    Implements Eq. (3.21) for condensate GE, Eq. (3.22) for Mw from
    API (or the caller may supply M_wo directly), and the book's
    7390 SCF/bbl water GE (p. 92). Eq. (3.23) rolls all pieces into
    total gas production.

    Args:
        Np_stb: Condensate production, STB (>= 0).
        gamma_o: Optional stock-tank oil specific gravity (water=1).
        M_wo: Optional oil molecular weight, lbm/lbmol (> 0).
        oil_api: Optional stock-tank API gravity; used to derive
            gamma_o and M_wo if not supplied.
        Wp_water_bbl: Produced water, bbl (>= 0; default 0).
        Gp_surf_scf: Separator + stock-tank gas, SCF (>= 0; default 0).

    Returns:
        GasEquivalentResult with GE, GE_water, Gp_total, Gw_total,
        gamma_o, M_wo.

    Raises:
        ValueError: invalid input or inability to resolve (gamma_o, M_wo).
    """
    if not (Np_stb >= 0.0):
        raise ValueError(f"Np_stb must be >= 0, got {Np_stb!r}")
    if not (Wp_water_bbl >= 0.0):
        raise ValueError(
            f"Wp_water_bbl must be >= 0, got {Wp_water_bbl!r}"
        )
    if not (Gp_surf_scf >= 0.0):
        raise ValueError(
            f"Gp_surf_scf must be >= 0, got {Gp_surf_scf!r}"
        )

    # Resolve gamma_o
    if gamma_o is not None:
        if not (0.0 < gamma_o < MW_GAMMA_DEN_OFFSET):
            raise ValueError(
                f"gamma_o must be in (0, {MW_GAMMA_DEN_OFFSET}), "
                f"got {gamma_o!r}"
            )
        gamma = float(gamma_o)
    elif oil_api is not None:
        if not (MW_API_OFFSET < oil_api < 100.0):
            raise ValueError(
                f"oil_api must be in ({MW_API_OFFSET}, 100), "
                f"got {oil_api!r}"
            )
        gamma = API_TO_SG_NUM / (API_TO_SG_DEN_OFFSET + oil_api)
    else:
        raise ValueError(
            "Provide at least one of gamma_o, oil_api, or M_wo"
        )

    # Resolve M_wo (direct, or from API, or from gamma_o)
    if M_wo is not None:
        if not (M_wo > 0.0):
            raise ValueError(f"M_wo must be > 0, got {M_wo!r}")
        mw = float(M_wo)
    elif oil_api is not None:
        if not (MW_API_OFFSET < oil_api < 100.0):
            raise ValueError(
                f"oil_api must be in ({MW_API_OFFSET}, 100), "
                f"got {oil_api!r}"
            )
        mw = MW_NUM / (oil_api - MW_API_OFFSET)
    else:
        # Derive Mw from gamma_o via the alternative form of Eq. 3.22
        mw = MW_GAMMA_NUM * gamma / (MW_GAMMA_DEN_OFFSET - gamma)

    ge = GE_COEFF * gamma / mw
    ge_water = GE_WATER

    gp_total = Gp_surf_scf + ge * Np_stb
    gw_total = ge_water * Wp_water_bbl

    # Validity: book notes (p. 92) Eq. 3.22 approximate; Mwo preferred
    # to be measured; typical valid condensate range 45-70 deg API.
    in_validity = True
    if oil_api is not None and not (30.0 <= oil_api <= 70.0):
        in_validity = False

    return GasEquivalentResult(
        ge_scf_per_bbl=ge,
        ge_water_scf_per_bbl=ge_water,
        gp_total_scf=gp_total,
        gw_total_scf=gw_total,
        gamma_o=gamma,
        mw_o=mw,
        in_validity=in_validity,
    )
