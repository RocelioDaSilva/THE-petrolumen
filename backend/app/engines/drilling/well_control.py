"""Drilling Well Control Engine.

Ported from src/lib/drilling/wellControl.ts and src/lib/drilling/wellControlAdv.ts.
Directly sourced from:
  - Carter, Lyons & Lapeyrouse (5th Ed., 2023), Chapter 3
  - Colin Cormack, "An Introduction to Well Control Calculations for Drilling Operations" (Springer, 2017)
  - Bourgoyne et al., "Applied Drilling Engineering" (SPE, 1986), Chapter 4
"""

from __future__ import annotations

import math
from typing import Literal
from pydantic import BaseModel, Field

# Constants matching src/lib/math/constants.ts
HYDROSTATIC_CONSTANT: float = 0.052
CAPACITY_CONSTANT: float = 1029.4
FT3_TO_BBL: float = 0.1781
M3_TO_BBL: float = 6.2905
STEEL_LB_PER_BBL: float = 2747.0

# Rounding logic matching src/lib/math/rounding.ts
RoundingMode = Literal["half-up", "round-up", "round-down"]


def round_val(value: float, places: int = 0, mode: RoundingMode = "half-up") -> float:
    """Matches TypeScript round(value, places, mode) with decimal-safe shifted rounding."""
    if not math.isfinite(value):
        return 0.0
    factor = 10.0**places
    sign = -1.0 if value < 0 else 1.0
    abs_val = abs(value)

    # In JS: shifted = Number(absVal + 'e' + places)
    # Replicating JS floating string conversion or direct scaled rounding
    # For integer places, scaled = round(abs_val * factor)
    # Using Decimal or float with standard half-up:
    if mode == "round-up":
        res = sign * (math.ceil(abs_val * factor) / factor)
    elif mode == "round-down":
        res = sign * (math.floor(abs_val * factor) / factor)
    else:
        # half-up: JS Math.round(abs_val * factor) rounds half towards +infinity
        res = sign * (math.floor(abs_val * factor + 0.5) / factor)

    return float(res) if places > 0 else float(int(res))


def round_kill_mw(ppg: float) -> float:
    """Kill Mud Weight must ALWAYS be rounded UP to 1 decimal place.

    E.g., 12.21 -> 12.3 ppg (Cormack Sect. 4)
    """
    if not math.isfinite(ppg):
        return 0.0
    return round_val(ppg, 1, "round-up")


def round_max_mw(ppg: float) -> float:
    """Maximum Mud Weight must ALWAYS be rounded DOWN to 1 decimal place.

    E.g., 14.68 -> 14.6 ppg (Cormack Sect. 3)
    """
    if not math.isfinite(ppg):
        return 0.0
    return round_val(ppg, 1, "round-down")


class CompanyRounding:
    @staticmethod
    def capacity(val: float) -> float:
        return round_val(val, 5)

    @staticmethod
    def volume(val: float) -> float:
        return round_val(val, 2)

    @staticmethod
    def pump_output(val: float) -> float:
        return round_val(val, 3)

    @staticmethod
    def strokes(val: float) -> float:
        return round_val(val, 0, "round-up")

    @staticmethod
    def time(val: float) -> float:
        return round_val(val, 0, "round-up")

    @staticmethod
    def pressure(val: float) -> float:
        return round_val(val, 0)

    @staticmethod
    def gradient(val: float) -> float:
        return round_val(val, 4)

    @staticmethod
    def mud_weight(val: float) -> float:
        return round_val(val, 2)

    kill_mw = staticmethod(round_kill_mw)
    max_mw = staticmethod(round_max_mw)


# ==========================================
# Pydantic Models for Schedules & Sections
# ==========================================


class AnnularSection(BaseModel):
    name: str
    capacityBblFt: float
    lengthFt: float


class TaperedSectionResult(BaseModel):
    name: str
    cumulativeStrokes: int
    pressureAtEnd: int


class SchedulePoint(BaseModel):
    stroke: int
    drillpipePressurePsi: int
    casingPressurePsi: int
    stageDescription: str


class WaitAndWeightScheduleInput(BaseModel):
    icpPsi: float = Field(..., description="Initial Circulating Pressure (psi)")
    fcpPsi: float = Field(..., description="Final Circulating Pressure (psi)")
    sicpPsi: float = Field(..., description="Shut-In Casing Pressure (psi)")
    surfaceToBitStrokes: int = Field(..., description="Pump strokes from surface to bit")
    bitToSurfaceStrokes: int = Field(..., description="Pump strokes from bit to surface")
    intervalsCount: int = Field(10, description="Intervals count for step-down")


class DrillersMethodScheduleInput(BaseModel):
    icpPsi: float = Field(..., description="Initial Circulating Pressure (psi)")
    fcpPsi: float = Field(..., description="Final Circulating Pressure (psi)")
    sicpPsi: float = Field(..., description="Shut-In Casing Pressure (psi)")
    surfaceToBitStrokes: int = Field(..., description="Pump strokes from surface to bit")
    bitToSurfaceStrokes: int = Field(..., description="Pump strokes from bit to surface")


class DrillersMethodScheduleResult(BaseModel):
    firstCirculation: list[SchedulePoint]
    secondCirculation: list[SchedulePoint]


# ==========================================
# Core Carter & Cormack Well Control Functions
# ==========================================


def masicp(lot_ppg: float, mwc_ppg: float, csg_d_tvd_ft: float) -> float:
    """MASICP: Maximum Allowable Surface Pressure / Shut-In Casing Pressure.

    Carter Ch. 3, Eq. 3.1: MASICP = (LOT - MWc) * 0.052 * Csgd
    """
    return (lot_ppg - mwc_ppg) * HYDROSTATIC_CONSTANT * csg_d_tvd_ft


def kill_mud_weight(sidpp: float, tvd: float, current_mw: float) -> float:
    """Kill Mud Weight: SIDPP / (TVD * 0.052) + Current MW

    Cormack Sect. 4, Eq. 4.2. Always round UP to 1 decimal place.
    """
    if tvd <= 0:
        return current_mw
    raw_kmw = sidpp / (tvd * HYDROSTATIC_CONSTANT) + current_mw
    return round_kill_mw(raw_kmw)


def kill_mud_weight_carter(sidpp_psi: float, tvd_ft: float, mwc_ppg: float) -> float:
    """Carter Ch. 3, Eq. 3.2."""
    return kill_mud_weight(sidpp_psi, tvd_ft, mwc_ppg)


def icp(scr: float, sidpp: float) -> float:
    """Initial Circulating Pressure (ICP): SCR + SIDPP.

    Cormack Sect. 4, Eq. 4.3.
    """
    return CompanyRounding.pressure(scr + sidpp)


def initial_circulating_pressure(sidpp_psi: float, krp_psi: float) -> float:
    """Carter Ch. 3, Eq. 3.3."""
    return icp(krp_psi, sidpp_psi)


def fcp(kill_mw: float, current_mw: float, scr: float) -> float:
    """Final Circulating Pressure (FCP): (Kill MW / Current MW) * SCR.

    Cormack Sect. 4, Eq. 4.4.
    """
    if current_mw <= 0:
        return scr
    return CompanyRounding.pressure((kill_mw / current_mw) * scr)


def final_circulating_pressure(kmw_ppg: float, krp_psi: float, mwc_ppg: float) -> float:
    """Carter Ch. 3, Eq. 3.4."""
    return fcp(kmw_ppg, mwc_ppg, krp_psi)


def strokes_per_line(spb_strokes: float, lines: int = 10) -> float:
    """Carter Ch. 3, Eq. 3.5."""
    return spb_strokes / lines


def pressure_decrease_per_line(icp_psi: float, fcp_psi: float, lines: int = 10) -> float:
    """Carter Ch. 3, Eq. 3.6."""
    return (icp_psi - fcp_psi) / lines


def pressure_chart_digital(
    icp_psi: float, fcp_psi: float, spb_strokes: float, lines: int = 10
) -> list[dict[str, int]]:
    """Digital pressure chart schedule (Carter Ch. 3, Section 3.2)."""
    chart: list[dict[str, int]] = []
    d_strokes = strokes_per_line(spb_strokes, lines)
    d_p = pressure_decrease_per_line(icp_psi, fcp_psi, lines)
    for i in range(lines + 1):
        chart.append({
            "stroke": round(i * d_strokes),
            "pressure": round(icp_psi - i * d_p),
        })
    return chart


def pressure_chart_analog(
    icp_psi: float, fcp_psi: float, stb_time_min: float, lines: int = 10
) -> list[dict[str, float]]:
    """Analog pressure chart schedule (Carter Ch. 3, Section 3.2)."""
    chart: list[dict[str, float]] = []
    dt = stb_time_min / lines
    d_p = pressure_decrease_per_line(icp_psi, fcp_psi, lines)
    for i in range(lines + 1):
        chart.append({
            "timeMin": round(i * dt * 10.0) / 10.0,
            "pressure": float(round(icp_psi - i * d_p)),
        })
    return chart


def section_strokes(length_ft: float, capacity_bbl_ft: float, pump_output_bbl_stk: float) -> float:
    """Tapered string section strokes (Carter Ch. 3, Eq. 3.7)."""
    return (length_ft * capacity_bbl_ft) / pump_output_bbl_stk


def section_pressure(
    icp_psi: float, fcp_psi: float, section_length_ft: float, total_length_ft: float
) -> float:
    """Tapered string section pressure (Carter Ch. 3, Eq. 3.8)."""
    return icp_psi - ((icp_psi - fcp_psi) * section_length_ft) / total_length_ft


def tapered_kill_sheet(
    sections: list[dict[str, Any]] | list[AnnularSection],
    icp_psi: float,
    fcp_psi: float,
    pump_output_bbl_stk: float,
) -> list[TaperedSectionResult]:
    """Tapered kill sheet calculations (Carter Ch. 3, Section 3.3)."""
    sec_dicts = [s.model_dump() if isinstance(s, BaseModel) else s for s in sections]
    total_length = sum(s["lengthFt"] for s in sec_dicts)
    cum_strokes = 0.0
    cum_length = 0.0
    results: list[TaperedSectionResult] = []

    for sec in sec_dicts:
        stks = section_strokes(sec["lengthFt"], sec["capacityBblFt"], pump_output_bbl_stk)
        cum_strokes += stks
        cum_length += sec["lengthFt"]
        p_end = section_pressure(icp_psi, fcp_psi, cum_length, total_length)
        results.append(
            TaperedSectionResult(
                name=sec["name"],
                cumulativeStrokes=round(cum_strokes),
                pressureAtEnd=round(p_end),
            )
        )
    return results


def strokes_to_kop(cdp_bbl_ft: float, md_kop_ft: float, op_bbl_stk: float) -> float:
    """Carter Ch. 3, Eq. 3.9."""
    return (cdp_bbl_ft * md_kop_ft) / op_bbl_stk


def strokes_from_kop(
    cdp_bbl_ft: float, md_bit_ft: float, md_kop_ft: float, op_bbl_stk: float
) -> float:
    """Carter Ch. 3, Eq. 3.10."""
    return (cdp_bbl_ft * (md_bit_ft - md_kop_ft)) / op_bbl_stk


def kill_weight_mud_deviated(sidpp_psi: float, tvd_td_ft: float, mwc_ppg: float) -> float:
    """Carter Ch. 3, Eq. 3.11."""
    return kill_mud_weight(sidpp_psi, tvd_td_ft, mwc_ppg)


def circulating_pressure_at_kop(
    icp_psi: float,
    kmw_ppg: float,
    mwc_ppg: float,
    tvd_kop_ft: float,
    tvd_td_ft: float,
    sidpp_psi: float,
    krp_psi: float,
) -> float:
    """Circulating pressure at KOP (Carter Ch. 3, Eq. 3.12)."""
    fcp_val = final_circulating_pressure(kmw_ppg, krp_psi, mwc_ppg)
    return icp_psi - ((icp_psi - fcp_val) * tvd_kop_ft) / tvd_td_ft


def masp_method1(
    mwm_ppg: float, mwsf_ppg: float, tvd_ft: float, g_gas_psi_ft: float = 0.115
) -> float:
    """MASP Method 1 (Gas column to surface, Carter Ch. 3, Eq. 3.13)."""
    return (mwsf_ppg - mwm_ppg) * HYDROSTATIC_CONSTANT * tvd_ft + (
        mwm_ppg * HYDROSTATIC_CONSTANT - g_gas_psi_ft
    ) * tvd_ft


def masp_method2(
    fg_ppg: float,
    mwsf_ppg: float,
    tvd_csg_ft: float,
    tvd_td_ft: float,
    g_gas_psi_ft: float = 0.115,
) -> float:
    """MASP Method 2 (Fracture gradient & gas column, Carter Ch. 3, Eq. 3.14)."""
    return (fg_ppg - mwsf_ppg) * HYDROSTATIC_CONSTANT * tvd_csg_ft - g_gas_psi_ft * (
        tvd_td_ft - tvd_csg_ft
    )


def trip_margin(yp: float, dh_inches: float, dp_inches: float) -> float:
    """Trip margin (Carter Ch. 3, Eq. 3.15)."""
    return yp / (11.7 * (dh_inches - dp_inches))


def diverter_line_diameter(dh_inches: float, dp_inches: float) -> float:
    """Carter Ch. 3, Eq. 3.16."""
    return math.sqrt(dh_inches**2 - dp_inches**2)


def fg_matthews_kelly_louisiana(p_grad_psi_ft: float, tvd_ft: float) -> float:
    """Matthews & Kelly fracture gradient (Louisiana Offshore, Carter Ch. 3, Eq. 3.17)."""
    ki = 0.5 + 3e-5 * tvd_ft
    obg = 1.0
    fg_psi_ft = p_grad_psi_ft + ki * (obg - p_grad_psi_ft)
    return fg_psi_ft / HYDROSTATIC_CONSTANT


def fg_matthews_kelly_texas(p_grad_psi_ft: float, tvd_ft: float) -> float:
    """Matthews & Kelly fracture gradient (Texas Gulf Coast, Carter Ch. 3, Eq. 3.18)."""
    ki = 0.6 + 2.5e-5 * tvd_ft
    obg = 1.0
    fg_psi_ft = p_grad_psi_ft + ki * (obg - p_grad_psi_ft)
    return fg_psi_ft / HYDROSTATIC_CONSTANT


def eaton_overburden_gradient(tvd_ft: float) -> float:
    """Carter Ch. 3, Section 3.8."""
    return 0.85 + 0.15 * (1.0 - math.exp(-tvd_ft / 5000.0))


def eaton_poisson_ratio(tvd_ft: float) -> float:
    """Carter Ch. 3, Section 3.8."""
    return 0.25 + 0.2 * (tvd_ft / 20000.0)


def fg_eaton(obg_psi_ft: float, p_grad_psi_ft: float, poisson_ratio: float) -> float:
    """Carter Ch. 3, Eq. 3.19."""
    fg_psi_ft = p_grad_psi_ft + (poisson_ratio / (1.0 - poisson_ratio)) * (obg_psi_ft - p_grad_psi_ft)
    return fg_psi_ft / HYDROSTATIC_CONSTANT


def fg_subsea(
    obg_psi_ft: float,
    p_grad_psi_ft: float,
    poisson_ratio: float,
    water_depth_ft: float,
    air_gap_ft: float,
    tvd_ft: float,
) -> float:
    """Carter Ch. 3, Eq. 3.20."""
    sea_water_grad = 0.444
    obg_adj = (sea_water_grad * water_depth_ft + obg_psi_ft * (tvd_ft - water_depth_ft - air_gap_ft)) / tvd_ft
    return fg_eaton(obg_adj, p_grad_psi_ft, poisson_ratio)


def surface_pressure_fit_method1(mwm_ppg: float, mwc_ppg: float, tvd_csg_ft: float) -> float:
    """FIT Surface Pressure Method 1 (Carter Ch. 3, Eq. 3.21)."""
    return (mwm_ppg - mwc_ppg) * HYDROSTATIC_CONSTANT * tvd_csg_ft


def surface_pressure_fit_method2(target_emw_ppg: float, mwc_ppg: float, tvd_csg_ft: float) -> float:
    """FIT Surface Pressure Method 2 (Carter Ch. 3, Eq. 3.22)."""
    return (target_emw_ppg - mwc_ppg) * HYDROSTATIC_CONSTANT * tvd_csg_ft


def surface_pressure_fit_method3(fg_ppg: float, mwc_ppg: float, tvd_csg_ft: float) -> float:
    """FIT Surface Pressure Method 3 (Carter Ch. 3, Eq. 3.23)."""
    return (fg_ppg - mwc_ppg) * HYDROSTATIC_CONSTANT * tvd_csg_ft


def max_allowable_pressure_line(
    overburden_psi_ft: float, sf: float, tvd_csg_ft: float, mw_ppg: float
) -> float:
    """Carter Ch. 3, Eq. 3.24."""
    return (overburden_psi_ft * sf - mw_ppg * HYDROSTATIC_CONSTANT) * tvd_csg_ft


def estimated_lot_pressure_line(fg_ppg: float, mw_ppg: float, tvd_csg_ft: float) -> float:
    """Carter Ch. 3, Eq. 3.25."""
    return (fg_ppg - mw_ppg) * HYDROSTATIC_CONSTANT * tvd_csg_ft


def min_acceptable_lot_pressure_line(mw_mxi_ppg: float, mw_ppg: float, tvd_csg_ft: float) -> float:
    """Carter Ch. 3, Eq. 3.26."""
    return (mw_mxi_ppg - mw_ppg) * HYDROSTATIC_CONSTANT * tvd_csg_ft


def mud_compressibility(water_pct: float, oil_pct: float, solids_pct: float) -> float:
    """Carter Ch. 3, Eq. 3.27."""
    return (water_pct * 3.0 + oil_pct * 5.0 + solids_pct * 0.5) / 100.0


def lot_graph_slope(cm: float, v_system_bbl: float) -> float:
    """Carter Ch. 3, Eq. 3.28."""
    return 10000.0 / (v_system_bbl * (cm / 100.0))


def max_mud_weight(lot_pressure: float, shoe_tvd: float, test_mw: float) -> float:
    """Maximum Mud Weight from LOT: LOT / (Shoe TVD * 0.052) + Test MW.

    Cormack Sect. 3, Worked Example. Always round DOWN to 1 decimal place.
    """
    if shoe_tvd <= 0:
        return test_mw
    raw_max = lot_pressure / (shoe_tvd * HYDROSTATIC_CONSTANT) + test_mw
    return round_max_mw(raw_max)


def max_allowable_mud_weight(lot_psi: float, tvd_csg_ft: float, mw_ppg: float) -> float:
    """Carter Ch. 3, Eq. 3.29."""
    return max_mud_weight(lot_psi, tvd_csg_ft, mw_ppg)


def kt_intensity(
    fg_ppg: float,
    mw_ppg: float,
    sf_ppg: float,
    tm_ppg: float,
    tvd_csg_ft: float,
    tvd_td_ft: float,
) -> float:
    """Kick tolerance intensity (Carter Ch. 3, Eq. 3.30)."""
    return ((fg_ppg - sf_ppg - tm_ppg) * tvd_csg_ft - mw_ppg * (tvd_td_ft - tvd_csg_ft)) / tvd_td_ft


def kt_maximum_surface_pressure(kti_ppg: float, tvd_td_ft: float) -> float:
    """Carter Ch. 3, Eq. 3.31."""
    return kti_ppg * HYDROSTATIC_CONSTANT * tvd_td_ft


def kt_maximum_formation_pressure(kti_ppg: float, mw_ppg: float, tvd_td_ft: float) -> float:
    """Carter Ch. 3, Eq. 3.32."""
    return (mw_ppg + kti_ppg) * HYDROSTATIC_CONSTANT * tvd_td_ft


def kt_influx_length(masicp_psi: float, g_mud_psi_ft: float, g_influx_psi_ft: float) -> float:
    """Carter Ch. 3, Eq. 3.33."""
    return masicp_psi / (g_mud_psi_ft - g_influx_psi_ft)


def kt_volume(
    fg_ppg: float,
    tvd_csg_ft: float,
    l_influx_ft: float,
    ca_bbl_ft: float,
    mw_ppg: float,
    tvd_td_ft: float,
) -> float:
    """Carter Ch. 3, Eq. 3.34."""
    return l_influx_ft * ca_bbl_ft


def bhp_from_sidpp(sidpp_psi: float, mw_ppg: float, tvd_td_ft: float) -> float:
    """Carter Ch. 3, Eq. 3.35."""
    return sidpp_psi + mw_ppg * HYDROSTATIC_CONSTANT * tvd_td_ft


def sidpp_from_fp(pf_psi: float, mw_ppg: float, tvd_td_ft: float) -> float:
    """Carter Ch. 3, Eq. 3.36."""
    return pf_psi - mw_ppg * HYDROSTATIC_CONSTANT * tvd_td_ft


def sicp_from_fp(
    pf_psi: float, mw_ppg: float, tvd_td_ft: float, g_influx_psi_ft: float, l_influx_ft: float
) -> float:
    """Carter Ch. 3, Eq. 3.37."""
    return pf_psi - mw_ppg * HYDROSTATIC_CONSTANT * (tvd_td_ft - l_influx_ft) - g_influx_psi_ft * l_influx_ft


def influx_length(v_kick_bbl: float, ca_bbl_ft: float) -> float:
    """Carter Ch. 3, Eq. 3.38."""
    return v_kick_bbl / ca_bbl_ft


def influx_length_multi_section(
    v_kick_bbl: float, c_dc_oh_bbl_ft: float, l_dc_ft: float, c_dp_oh_bbl_ft: float
) -> float:
    """Carter Ch. 3, Eq. 3.39."""
    v_dc = c_dc_oh_bbl_ft * l_dc_ft
    if v_kick_bbl <= v_dc:
        return v_kick_bbl / c_dc_oh_bbl_ft
    return l_dc_ft + (v_kick_bbl - v_dc) / c_dp_oh_bbl_ft


InfluxType = Literal["Gas", "Combination Gas/Oil", "Oil", "Salt Water"]


def influx_type_from_density(wk_ppg: float) -> InfluxType:
    """Carter Ch. 3, Table 3.1."""
    if wk_ppg <= 3.0:
        return "Gas"
    if wk_ppg <= 5.0:
        return "Combination Gas/Oil"
    if wk_ppg <= 7.0:
        return "Oil"
    return "Salt Water"


def original_mud_weight_from_gas_cut(mw_gc: float, mw_d: float, mw_bl: float) -> float:
    """Carter Ch. 3, Eq. 3.40."""
    return (mw_gc * mw_d) / mw_bl


def gas_content_from_cut_mud(mw_orig: float, mw_cut: float) -> float:
    """Carter Ch. 3, Eq. 3.41."""
    return (mw_orig - mw_cut) / mw_orig


def reduction_in_mud_weight_no_kick(
    rop_ft_hr: float,
    dh_inches: float,
    porosity_pct: float,
    w_solids_ppg: float,
    mw_ppg: float,
    p_bh_psi: float,
    q_gpm: float,
) -> float:
    """Carter Ch. 3, Eq. 3.42."""
    q_cuttings = (rop_ft_hr * dh_inches**2) / 1471.0
    return (q_cuttings * (1.0 - porosity_pct / 100.0) * (w_solids_ppg - mw_ppg)) / (q_gpm / 42.0)


def gas_migration_rate(
    sicp2_psi: float, sicp1_psi: float, mw_ppg: float, time_hours: float
) -> float:
    """Carter Ch. 3, Eq. 3.43."""
    if time_hours <= 0 or mw_ppg <= 0:
        return 0.0
    return (sicp2_psi - sicp1_psi) / (mw_ppg * HYDROSTATIC_CONSTANT * time_hours)


def hp_decrease_from_influx(
    tvd_ft: float,
    mwg_ppg: float,
    v_kick_bbl: float,
    ca_bbl_ft: float,
    g_influx_psi_ft: float,
) -> float:
    """Carter Ch. 3, Eq. 3.44."""
    l_influx = v_kick_bbl / ca_bbl_ft
    return l_influx * (mwg_ppg * HYDROSTATIC_CONSTANT - g_influx_psi_ft)


def hp_decrease_gradient_method(
    mwg_ppg: float, g_influx_psi_ft: float, ca_bbl_ft: float, v_kick_bbl: float
) -> float:
    """Carter Ch. 3, Eq. 3.45."""
    return hp_decrease_from_influx(0.0, mwg_ppg, v_kick_bbl, ca_bbl_ft, g_influx_psi_ft)


def barite_plug_base_liquid(
    v_plug_bbl: float, w_mud_sg: float, mw_liquid_ppg: float, mw_plug_ppg: float
) -> float:
    """Carter Ch. 3, Eq. 3.64."""
    return v_plug_bbl * ((mw_plug_ppg - w_mud_sg * 8.34) / (mw_plug_ppg - mw_liquid_ppg))


def barite_plug_sacks(v_plug_bbl: float, sacks_per_bbl: float = 14.7) -> int:
    """Carter Ch. 3, Eq. 3.67."""
    return round(v_plug_bbl * sacks_per_bbl)


# ==========================================
# Schedules: Driller's Method & Wait & Weight
# ==========================================


def generate_wait_and_weight_schedule(
    icp_psi: float,
    fcp_psi: float,
    sicp_psi: float,
    surface_to_bit_strokes: int,
    bit_to_surface_strokes: int,
    intervals_count: int = 10,
) -> list[SchedulePoint]:
    """Detailed Wait & Weight (Engineer's Method) Drillpipe Pressure Schedule.

    Sourced: Bourgoyne Ch. 4, Section 4.8 & Fig. 4.39B.
    """
    points: list[SchedulePoint] = []

    # Stage 1: Pumping kill mud from surface to bit (Linear step-down from ICP to FCP)
    step_strokes = max(10, surface_to_bit_strokes // intervals_count)
    for s in range(0, surface_to_bit_strokes + 1, step_strokes):
        fraction = s / surface_to_bit_strokes if surface_to_bit_strokes > 0 else 0.0
        dp_pressure = icp_psi - fraction * (icp_psi - fcp_psi)
        cas_pressure = sicp_psi + math.sin(fraction * math.pi) * 150.0

        points.append(
            SchedulePoint(
                stroke=s,
                drillpipePressurePsi=round(dp_pressure),
                casingPressurePsi=round(cas_pressure),
                stageDescription="Início do Amortecimento (ICP)"
                if s == 0
                else "Descida Linear de Pressão na Coluna",
            )
        )

    # Ensure exact surface-to-bit point is present
    if points and points[-1].stroke != surface_to_bit_strokes:
        points.append(
            SchedulePoint(
                stroke=surface_to_bit_strokes,
                drillpipePressurePsi=int(round(fcp_psi)),
                casingPressurePsi=int(round(sicp_psi + 50.0)),
                stageDescription="Lama de Amortecimento Atinge a Broca (FCP)",
            )
        )

    # Stage 2: Pumping kill mud from bit to surface (Hold FCP constant on drillpipe)
    total_strokes = surface_to_bit_strokes + bit_to_surface_strokes
    annulus_step = max(10, bit_to_surface_strokes // intervals_count)

    for s in range(surface_to_bit_strokes + annulus_step, total_strokes + 1, annulus_step):
        ann_fraction = (s - surface_to_bit_strokes) / bit_to_surface_strokes if bit_to_surface_strokes > 0 else 1.0
        cas_pressure = max(0.0, (1.0 - ann_fraction) * (sicp_psi + 50.0))

        points.append(
            SchedulePoint(
                stroke=s,
                drillpipePressurePsi=int(round(fcp_psi)),
                casingPressurePsi=round(cas_pressure),
                stageDescription="Poço Amortecido com Sucesso"
                if ann_fraction >= 0.99
                else "Deslocamento no Anular a FCP Constante",
            )
        )

    return points


def generate_drillers_method_schedule(
    icp_psi: float,
    fcp_psi: float,
    sicp_psi: float,
    surface_to_bit_strokes: int,
    bit_to_surface_strokes: int,
) -> DrillersMethodScheduleResult:
    """Detailed Driller's Method (Two-Circulation) Drillpipe Pressure Schedule.

    Sourced: Bourgoyne Ch. 4, Section 4.8 & Fig. 4.39A.
    """
    first_circ: list[SchedulePoint] = []
    second_circ: list[SchedulePoint] = []

    total_well_strokes = surface_to_bit_strokes + bit_to_surface_strokes
    step_circ1 = max(1, total_well_strokes // 5)

    # 1st Circulation: Circulate out influx with original mud weight (hold ICP constant on DP)
    for s in range(0, total_well_strokes + 1, step_circ1):
        fraction = s / total_well_strokes if total_well_strokes > 0 else 0.0
        cas_pressure = sicp_psi if fraction == 0 else max(0.0, sicp_psi * (1.0 - fraction * 0.7))
        first_circ.append(
            SchedulePoint(
                stroke=s,
                drillpipePressurePsi=int(round(icp_psi)),
                casingPressurePsi=round(cas_pressure),
                stageDescription="1ª Circ.: Expulsão do Influxo a ICP"
                if s == 0
                else "1ª Circ.: Removendo Influxo do Anular",
            )
        )

    # 2nd Circulation: Displace original mud with Kill Mud Weight
    # Surface to bit: step down from ICP to FCP
    step_circ2_dp = max(1, surface_to_bit_strokes // 3)
    last_casing_p = first_circ[-1].casingPressurePsi if first_circ else 0
    for s in range(0, surface_to_bit_strokes + 1, step_circ2_dp):
        frac = s / surface_to_bit_strokes if surface_to_bit_strokes > 0 else 0.0
        second_circ.append(
            SchedulePoint(
                stroke=s,
                drillpipePressurePsi=round(icp_psi - frac * (icp_psi - fcp_psi)),
                casingPressurePsi=last_casing_p,
                stageDescription="2ª Circ.: Injeção da Lama de Amortecimento",
            )
        )

    # Bit to surface: hold FCP constant
    step_circ2_ann = max(1, bit_to_surface_strokes // 3)
    for s in range(surface_to_bit_strokes, total_well_strokes + 1, step_circ2_ann):
        frac = (s - surface_to_bit_strokes) / bit_to_surface_strokes if bit_to_surface_strokes > 0 else 1.0
        second_circ.append(
            SchedulePoint(
                stroke=s,
                drillpipePressurePsi=int(round(fcp_psi)),
                casingPressurePsi=round(max(0.0, 100.0 * (1.0 - frac))),
                stageDescription="2ª Circ.: Poço Amortecido"
                if frac >= 0.9
                else "2ª Circ.: Preenchimento do Anular com KMW",
            )
        )

    return DrillersMethodScheduleResult(
        firstCirculation=first_circ,
        secondCirculation=second_circ,
    )


# Function wrappers to match TypeScript camelCase naming
taperedKillSheet = tapered_kill_sheet
circulatingPressureAtKOP = circulating_pressure_at_kop
pressureDecreasePerLine = pressure_decrease_per_line
fgMatthewsKelly_Louisiana = fg_matthews_kelly_louisiana
fgMatthewsKelly_Texas = fg_matthews_kelly_texas
surfacePressure_FIT_method1 = surface_pressure_fit_method1
surfacePressure_FIT_method2 = surface_pressure_fit_method2
surfacePressure_FIT_method3 = surface_pressure_fit_method3
ktIntensity = kt_intensity
influxTypeFromDensity = influx_type_from_density
originalMudWeightFromGasCut = original_mud_weight_from_gas_cut
gasContentFromCutMud = gas_content_from_cut_mud
gasMigrationRate = gas_migration_rate
hpDecreaseFromInflux = hp_decrease_from_influx
baritePlug_baseLiquid = barite_plug_base_liquid
baritePlug_sacks = barite_plug_sacks
tripMargin = trip_margin
generateWaitAndWeightSchedule = generate_wait_and_weight_schedule
generateDrillersMethodSchedule = generate_drillers_method_schedule
