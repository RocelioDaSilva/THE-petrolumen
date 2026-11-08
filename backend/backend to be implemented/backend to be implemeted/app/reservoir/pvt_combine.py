"""Combine flash + differential + separator PVT data into Bo and Rso.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 6, Sec. 5, pp. 200-201, Eqs. (6.6)-(6.8),
worked examples on p. 201.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Regime = Literal["above_pb", "below_pb"]


@dataclass(frozen=True)
class PVTCombineResult:
    bo_bbl_stb: float
    rso_scf_stb: float
    regime: Regime


def oil_pvt_from_lab(
    p_psia: float,
    pb_psia: float,
    Bob: float,
    Bodb: float,
    Rsob: float,
    Rsodb: float,
    RV: float | None = None,
    Bod_current: float | None = None,
    Rsod_current: float | None = None,
) -> PVTCombineResult:
    """Combine flash + differential + separator data into Bo and Rso.

    Implements Eqs. (6.6)-(6.7) and the worked-example form of
    Eq. (6.8) from Craft, Hawkins, Terry (1991), Ch. 6, Sec. 5,
    pp. 200-201. Above bubble point: Bo = RV*Bob, Rso = Rsob.
    Below bubble point: Bo = Bod*(Bob/Bodb), Rso = Rsob -
    (Rsodb-Rsod)*(Bob/Bod).

    Args:
        p_psia: Pressure of interest, psia (> 0).
        pb_psia: Bubble-point pressure, psia (> 0).
        Bob: FVF at pb from separator tests, bbl/STB (> 0).
        Bodb: FVF at pb from differential test, bbl/STB (> 0).
        Rsob: Separator + stock-tank GOR at pb, SCF/STB (>= 0).
        Rsodb: Differential GOR at pb, SCF/STB (>= 0).
        RV: Flash relative volume V/Vb, dimensionless (> 0).
            Required if p_psia >= pb_psia.
        Bod_current: Differential FVF at p, bbl/STB (> 0).
            Required if p_psia < pb_psia.
        Rsod_current: Differential GOR at p, SCF/STB (>= 0).
            Required if p_psia < pb_psia.

    Returns:
        PVTCombineResult(bo_bbl_stb, rso_scf_stb, regime).

    Raises:
        ValueError: any input out of range, or required argument
            missing for the pressure regime.
    """
    if not (p_psia > 0.0):
        raise ValueError(f"p_psia must be > 0, got {p_psia!r}")
    if not (pb_psia > 0.0):
        raise ValueError(f"pb_psia must be > 0, got {pb_psia!r}")
    if not (Bob > 0.0):
        raise ValueError(f"Bob must be > 0, got {Bob!r}")
    if not (Bodb > 0.0):
        raise ValueError(f"Bodb must be > 0, got {Bodb!r}")
    if not (Rsob >= 0.0):
        raise ValueError(f"Rsob must be >= 0, got {Rsob!r}")
    if not (Rsodb >= 0.0):
        raise ValueError(f"Rsodb must be >= 0, got {Rsodb!r}")

    if p_psia >= pb_psia:
        if RV is None:
            raise ValueError(
                "RV (flash V/Vb) is required above bubble point"
            )
        if not (RV > 0.0):
            raise ValueError(f"RV must be > 0, got {RV!r}")
        bo = RV * Bob
        rso = Rsob
        return PVTCombineResult(
            bo_bbl_stb=bo, rso_scf_stb=rso, regime="above_pb",
        )

    # Below bubble point
    if Bod_current is None or Rsod_current is None:
        raise ValueError(
            "Bod_current and Rsod_current are required below bubble point"
        )
    if not (Bod_current > 0.0):
        raise ValueError(
            f"Bod_current must be > 0, got {Bod_current!r}"
        )
    if not (Rsod_current >= 0.0):
        raise ValueError(
            f"Rsod_current must be >= 0, got {Rsod_current!r}"
        )

    # Eq. (6.7): Bo below Pb
    bo = Bod_current * (Bob / Bodb)
    # Worked-example form of Eq. (6.8) from p. 201
    rso = Rsob - (Rsodb - Rsod_current) * (Bob / Bod_current)

    return PVTCombineResult(
        bo_bbl_stb=bo, rso_scf_stb=rso, regime="below_pb",
    )
