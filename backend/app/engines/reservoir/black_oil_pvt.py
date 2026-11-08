"""Black-oil and formation-water PVT correlations from Craft et al. (1991).

The correlations return validity flags rather than silently treating a
numerically evaluable result as accurate outside its published fit range.
Units are field units as stated by the input/output names.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

_MIN_T_F = -459.67
_API_MIN_PHYSICAL = -10.0
_API_MAX_PHYSICAL = 100.0


@dataclass(frozen=True)
class GasViscosityResult:
    mu_cp: float
    rho_gcc: float
    molecular_weight_g_mol: float
    z_factor: float
    k_factor: float
    x_factor: float
    y_factor: float
    in_validity_range: bool


@dataclass(frozen=True)
class OilRsoResult:
    rso_scf_stb: float
    y_g: float
    clamped: bool
    in_validity_range: bool


@dataclass(frozen=True)
class OilBoResult:
    bo_bbl_stb: float
    f_term: float
    oil_specific_gravity: float
    rso_scf_stb: float
    clamped: bool
    in_validity_range: bool
    co_used_psi_inv: float | None


@dataclass(frozen=True)
class OilCompressibilityResult:
    co_psi_inv: float
    formulation: Literal["villena_lanzi", "vasquez_beggs"]
    rsob_scf_stb: float
    in_validity_range: bool


@dataclass(frozen=True)
class OilViscosityResult:
    mu_cp: float
    mu_dead_cp: float
    mu_at_bubble_point_cp: float
    a_factor: float
    b_factor: float
    m_exponent: float | None
    formulation: Literal["beggs_robinson", "vasquez_beggs"]
    rso_scf_stb: float
    in_validity_range: bool


@dataclass(frozen=True)
class WaterPVTResult:
    bw_bbl_stb: float
    rswp_scf_stb: float
    rsw_scf_stb: float
    cw_psi_inv: float
    mu_w_cp: float
    bw_in_validity_range: bool | None
    rsw_in_validity_range: bool
    cw_in_validity_range: bool
    mu_w_in_validity_range: bool


def gas_viscosity(
    p_psia: float,
    temperature_f: float,
    z_factor: float,
    *,
    gas_sg: float | None = None,
    molecular_weight_g_mol: float | None = None,
) -> GasViscosityResult:
    """Return Lee-Gonzalez-Eakin gas viscosity and intermediate values.

    Exactly one of gas specific gravity (air=1) and molecular weight is
    required. ``z_factor`` must be calculated at the supplied pressure and
    temperature, using an appropriate gas composition/correlation.
    """
    _require_finite_positive("p_psia", p_psia)
    _require_finite_above("temperature_f", temperature_f, _MIN_T_F)
    _require_finite_positive("z_factor", z_factor)
    if (gas_sg is None) == (molecular_weight_g_mol is None):
        raise ValueError(
            "Provide exactly one of gas_sg or molecular_weight_g_mol"
        )
    if gas_sg is not None:
        _require_finite_positive("gas_sg", gas_sg)
        if gas_sg >= 2.0:
            raise ValueError("gas_sg must be less than 2")
        molecular_weight = 28.97 * gas_sg
    else:
        if molecular_weight_g_mol is None:
            raise ValueError("molecular_weight_g_mol is required when gas_sg is omitted")
        _require_finite_positive("molecular_weight_g_mol", molecular_weight_g_mol)
        molecular_weight = float(molecular_weight_g_mol)

    temperature_r = temperature_f + 459.67
    density_gcc = 1.4935e-3 * p_psia * molecular_weight / (
        z_factor * temperature_r
    )
    k_factor = (
        (9.4 + 0.02 * molecular_weight) * temperature_r**1.5
        / (209.0 + 19.0 * molecular_weight + temperature_r)
    )
    x_factor = 3.5 + 986.0 / temperature_r + 0.01 * molecular_weight
    y_factor = 2.4 - 0.2 * x_factor
    rho_power_y = (
        0.0 if density_gcc == 0.0
        else math.exp(y_factor * math.log(density_gcc))
    )
    viscosity = 1.0e-4 * k_factor * math.exp(x_factor * rho_power_y)
    _require_result_positive("gas viscosity", viscosity)

    return GasViscosityResult(
        mu_cp=viscosity,
        rho_gcc=density_gcc,
        molecular_weight_g_mol=molecular_weight,
        z_factor=z_factor,
        k_factor=k_factor,
        x_factor=x_factor,
        y_factor=y_factor,
        in_validity_range=(
            100.0 <= p_psia <= 8000.0
            and 100.0 <= temperature_f <= 340.0
        ),
    )


def oil_solution_gor(
    p_psia: float,
    pb_psia: float,
    temperature_f: float,
    gas_sg: float,
    oil_api: float,
) -> OilRsoResult:
    """Return Standing/Beggs solution GOR, clamped to Rso at bubble point."""
    _validate_oil_inputs(p_psia, pb_psia, temperature_f, gas_sg, oil_api)
    y_g = 0.00091 * temperature_f - 0.0125 * oil_api
    reference_pressure = min(p_psia, pb_psia)
    rso = gas_sg * (
        reference_pressure / (18.0 * 10.0**y_g)
    ) ** 1.204
    if not math.isfinite(rso) or rso < 0:
        raise ValueError("Standing correlation produced non-physical solution GOR")
    return OilRsoResult(
        rso_scf_stb=rso,
        y_g=y_g,
        clamped=p_psia > pb_psia,
        in_validity_range=(
            130.0 <= pb_psia <= 7000.0
            and 100.0 <= temperature_f <= 258.0
            and 0.59 <= gas_sg <= 0.95
            and 16.5 <= oil_api <= 63.8
            and 20.0 <= rso <= 1425.0
        ),
    )


def oil_compressibility(
    p_psia: float,
    pb_psia: float,
    temperature_f: float,
    gas_sg: float,
    oil_api: float,
) -> OilCompressibilityResult:
    """Return Villena-Lanzi (p <= pb) or Vasquez-Beggs (p > pb) ``co``.

    The Villena-Lanzi correlation's printed temperature unit is ambiguous
    because it appears inside a logarithm. This implementation uses absolute
    temperature in Rankine, as specified by the reference document's example.
    """
    _validate_oil_inputs(p_psia, pb_psia, temperature_f, gas_sg, oil_api)
    rsob = oil_solution_gor(
        pb_psia, pb_psia, temperature_f, gas_sg, oil_api
    ).rso_scf_stb

    if p_psia <= pb_psia:
        if temperature_f <= _MIN_T_F or oil_api <= 0.0 or rsob <= 0.0:
            raise ValueError(
                "Villena-Lanzi requires positive absolute temperature, API, "
                "and bubble-point solution GOR"
            )
        log_co = (
            -0.664
            - 1.430 * math.log(p_psia)
            - 0.395 * math.log(pb_psia)
            + 0.390 * math.log(temperature_f + 459.67)
            + 0.455 * math.log(rsob)
            + 0.262 * math.log(oil_api)
        )
        co = math.exp(log_co)
        formulation: Literal["villena_lanzi", "vasquez_beggs"] = "villena_lanzi"
        in_range = (
            500.0 <= p_psia <= 5300.0
            and 763.0 <= pb_psia <= 5300.0
            and 78.0 <= temperature_f <= 330.0
            and 1.5 <= rsob <= 1947.0
            and 6.0 <= oil_api <= 52.0
            and 0.58 <= gas_sg <= 1.20
        )
    else:
        numerator = (
            5.0 * rsob
            + 17.2 * temperature_f
            - 1180.0 * gas_sg
            + 12.61 * oil_api
            - 1433.0
        )
        if numerator <= 0.0:
            raise ValueError(
                f"Vasquez-Beggs numerator = {numerator:.6g} <= 0; "
                "inputs produce non-physical oil compressibility"
            )
        co = numerator / (p_psia * 1.0e5)
        formulation = "vasquez_beggs"
        in_range = (
            126.0 <= p_psia <= 9500.0
            and 9.3 <= rsob <= 2199.0
            and 15.3 <= oil_api <= 59.5
            and 0.511 <= gas_sg <= 1.351
        )

    _require_result_positive("oil compressibility", co)
    return OilCompressibilityResult(co, formulation, rsob, in_range)


def oil_formation_volume_factor(
    p_psia: float,
    pb_psia: float,
    temperature_f: float,
    gas_sg: float,
    oil_api: float,
    co_psi_inv: float | None = None,
) -> OilBoResult:
    """Return Standing/Beggs oil FVF below and above the bubble point."""
    _validate_oil_inputs(p_psia, pb_psia, temperature_f, gas_sg, oil_api)
    oil_sg = 141.5 / (131.5 + oil_api)
    clamped = p_psia > pb_psia
    rso = oil_solution_gor(
        min(p_psia, pb_psia), pb_psia, temperature_f, gas_sg, oil_api
    ).rso_scf_stb
    f_term = rso * math.sqrt(gas_sg / oil_sg) + 1.25 * temperature_f
    if f_term <= 0:
        raise ValueError("Standing Bo correlation requires a positive F term")
    bo_at_reference = 0.972 + 0.000147 * f_term**1.175

    co_used: float | None = None
    if clamped:
        if co_psi_inv is None:
            co_used = oil_compressibility(
                p_psia, pb_psia, temperature_f, gas_sg, oil_api
            ).co_psi_inv
        else:
            _require_finite_positive("co_psi_inv", co_psi_inv)
            co_used = float(co_psi_inv)
        try:
            bo = bo_at_reference * math.exp(co_used * (pb_psia - p_psia))
        except OverflowError as exc:
            raise ValueError("Oil FVF calculation overflowed") from exc
    else:
        bo = bo_at_reference
    _require_result_positive("oil formation volume factor", bo)

    in_range = (
        130.0 <= pb_psia <= 7000.0
        and 100.0 <= temperature_f <= 258.0
        and 16.5 <= oil_api <= 63.8
        and 0.59 <= gas_sg <= 0.95
        and 1.024 <= bo <= 2.05
        and 20.0 <= rso <= 1425.0
    )
    return OilBoResult(
        bo_bbl_stb=bo,
        f_term=f_term,
        oil_specific_gravity=oil_sg,
        rso_scf_stb=rso,
        clamped=clamped,
        in_validity_range=in_range,
        co_used_psi_inv=co_used,
    )


def oil_viscosity(
    p_psia: float,
    pb_psia: float,
    temperature_f: float,
    gas_sg: float,
    oil_api: float,
) -> OilViscosityResult:
    """Return Egbogah/Beggs-Robinson/Vasquez-Beggs oil viscosity."""
    _validate_oil_inputs(p_psia, pb_psia, temperature_f, gas_sg, oil_api)
    if temperature_f <= 0.0:
        raise ValueError(
            "temperature_f must be > 0 degF for the Egbogah log10(T) term"
        )

    egbogah_log = (
        1.8653 - 0.025086 * oil_api - 0.5644 * math.log10(temperature_f)
    )
    try:
        mu_dead = 10.0 ** (10.0 ** egbogah_log) - 1.0
    except OverflowError as exc:
        raise ValueError("Egbogah correlation overflowed") from exc
    _require_result_positive("Egbogah dead-oil viscosity", mu_dead)

    reference_pressure = min(p_psia, pb_psia)
    rso = oil_solution_gor(
        reference_pressure, pb_psia, temperature_f, gas_sg, oil_api
    ).rso_scf_stb
    a_factor = 10.715 * (rso + 100.0) ** -0.515
    b_factor = 5.44 * (rso + 150.0) ** -0.338
    mu_at_pb = a_factor * math.exp(b_factor * math.log(mu_dead))

    if p_psia <= pb_psia:
        mu = mu_at_pb
        m_exponent = None
        formulation: Literal["beggs_robinson", "vasquez_beggs"] = (
            "beggs_robinson"
        )
        in_range = (
            0.0 < p_psia <= 5250.0
            and 70.0 <= temperature_f <= 295.0
            and 20.0 <= rso <= 2070.0
            and 16.0 <= oil_api <= 58.0
            and 59.0 <= temperature_f <= 176.0
            and 5.0 <= oil_api <= 58.0
        )
    else:
        m_exponent = (
            2.6 * p_psia**1.187 * math.exp(-11.513 - 8.98e-5 * p_psia)
        )
        try:
            mu = mu_at_pb * (p_psia / pb_psia) ** m_exponent
        except OverflowError as exc:
            raise ValueError("Vasquez-Beggs oil viscosity calculation overflowed") from exc
        formulation = "vasquez_beggs"
        in_range = (
            126.0 <= p_psia <= 9500.0
            and 0.117 <= mu <= 148.0
            and 9.3 <= rso <= 2199.0
            and 15.3 <= oil_api <= 59.5
            and 0.511 <= gas_sg <= 1.351
        )
    _require_result_positive("live-oil viscosity", mu)
    return OilViscosityResult(
        mu_cp=mu,
        mu_dead_cp=mu_dead,
        mu_at_bubble_point_cp=mu_at_pb,
        a_factor=a_factor,
        b_factor=b_factor,
        m_exponent=m_exponent,
        formulation=formulation,
        rso_scf_stb=rso,
        in_validity_range=in_range,
    )


def water_pvt(
    p_psia: float,
    temperature_f: float,
    salinity_pct: float,
    c_nacl_g_l: float | None = None,
) -> WaterPVTResult:
    """Return McCain/Osif water FVF, solution GWR, compressibility, viscosity.

    The below-bubble-point water-compressibility correction (Eq. 1.41) is
    intentionally omitted: the cited source describes it as unverified.
    """
    _require_finite_positive("p_psia", p_psia)
    _require_finite_positive("temperature_f", temperature_f)
    _require_finite("salinity_pct", salinity_pct)
    if not 0.0 < salinity_pct < 40.0:
        raise ValueError("salinity_pct must be in (0, 40)")
    c_nacl = 10.0 * salinity_pct if c_nacl_g_l is None else c_nacl_g_l
    _require_finite("c_nacl_g_l", c_nacl)
    if not 0.0 <= c_nacl <= 200.0:
        raise ValueError("c_nacl_g_l must be in [0, 200]")

    d_v_w_t = -1.00010e-2 + 1.33391e-4 * temperature_f + 5.50654e-7 * temperature_f**2
    d_v_w_p = (
        -1.95301e-9 * p_psia * temperature_f
        - 1.72834e-13 * p_psia**2 * temperature_f
        - 3.58922e-7 * p_psia
        - 2.25341e-10 * p_psia**2
    )
    bw = (1.0 + d_v_w_t) * (1.0 + d_v_w_p)

    a = (
        8.15839
        - 6.12265e-2 * temperature_f
        + 1.91663e-4 * temperature_f**2
        - 2.1654e-7 * temperature_f**3
    )
    b = (
        1.01021e-2
        - 7.44241e-5 * temperature_f
        + 3.05553e-7 * temperature_f**2
        - 2.94883e-10 * temperature_f**3
    )
    c = -1.0e-7 * (
        9.02505
        - 0.130237 * temperature_f
        + 8.53425e-4 * temperature_f**2
        - 2.34122e-6 * temperature_f**3
        + 2.37049e-9 * temperature_f**4
    )
    rswp = a + b * p_psia + c * p_psia**2
    if rswp < 0.0:
        raise ValueError(
            f"McCain Eq. 1.39 produced negative Rswp={rswp:.6g}; "
            "inputs are outside its useful range"
        )
    salinity_ratio = 10.0 ** (
        -0.0840655 * salinity_pct * temperature_f**-0.285854
    )
    rsw = rswp * salinity_ratio

    cw_denominator = (
        7.033 * p_psia + 541.5 * c_nacl - 537.0 * temperature_f + 403300.0
    )
    if cw_denominator <= 0.0:
        raise ValueError(
            "Osif Eq. 1.40 denominator is non-positive; "
            "water compressibility would be non-physical"
        )
    cw = 1.0 / cw_denominator

    salinity_sq = salinity_pct**2
    a_mu = (
        109.574 - 8.40564 * salinity_pct + 0.313314 * salinity_sq
        + 8.72213e-3 * salinity_sq * salinity_pct
    )
    b_mu = (
        -1.12166 + 2.63951e-2 * salinity_pct
        - 6.79461e-4 * salinity_sq
        - 5.47119e-5 * salinity_sq * salinity_pct
        + 1.55586e-6 * salinity_sq**2
    )
    mu_atmospheric = a_mu * temperature_f**b_mu
    pressure_ratio = 0.9994 + 4.0295e-5 * p_psia + 3.1062e-9 * p_psia**2
    mu_w = mu_atmospheric * pressure_ratio

    for label, value in (
        ("water FVF", bw),
        ("Rsw", rsw),
        ("water compressibility", cw),
        ("water viscosity", mu_w),
    ):
        _require_result_positive(label, value)
    return WaterPVTResult(
        bw_bbl_stb=bw,
        rswp_scf_stb=rswp,
        rsw_scf_stb=rsw,
        cw_psi_inv=cw,
        mu_w_cp=mu_w,
        # The reference does not give a closed numeric envelope for Bw.
        bw_in_validity_range=None,
        rsw_in_validity_range=(
            1000.0 <= p_psia <= 10000.0
            and 100.0 <= temperature_f <= 340.0
            and 0.0 < salinity_pct < 30.0
        ),
        cw_in_validity_range=(
            1000.0 <= p_psia <= 20000.0
            and 0.0 <= c_nacl <= 200.0
            and 200.0 <= temperature_f <= 270.0
        ),
        mu_w_in_validity_range=86.0 <= temperature_f <= 167.0,
    )


def _validate_oil_inputs(
    p_psia: float,
    pb_psia: float,
    temperature_f: float,
    gas_sg: float,
    oil_api: float,
) -> None:
    _require_finite_positive("p_psia", p_psia)
    _require_finite_positive("pb_psia", pb_psia)
    _require_finite_above("temperature_f", temperature_f, _MIN_T_F)
    _require_finite_positive("gas_sg", gas_sg)
    if gas_sg >= 2.0:
        raise ValueError("gas_sg must be less than 2")
    _require_finite("oil_api", oil_api)
    if not _API_MIN_PHYSICAL < oil_api < _API_MAX_PHYSICAL:
        raise ValueError(
            f"oil_api must be in ({_API_MIN_PHYSICAL}, {_API_MAX_PHYSICAL})"
        )


def _require_finite(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


def _require_finite_positive(name: str, value: float) -> None:
    _require_finite(name, value)
    if value <= 0.0:
        raise ValueError(f"{name} must be positive")


def _require_finite_above(name: str, value: float, lower_bound: float) -> None:
    _require_finite(name, value)
    if value <= lower_bound:
        raise ValueError(f"{name} must be greater than {lower_bound}")


def _require_result_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} correlation returned non-physical value {value!r}")
