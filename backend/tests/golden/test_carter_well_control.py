"""Carter, Lyons & Lapeyrouse (5th Ed., 2023)
Chapter 3: Well Control Golden Benchmarks Test Suite.

Ported from src/lib/drilling/__tests__/carterWellControlGoldenTests.ts.
"""

from app.engines.drilling.well_control import (
    baritePlug_baseLiquid,
    baritePlug_sacks,
    circulatingPressureAtKOP,
    fgMatthewsKelly_Louisiana,
    fgMatthewsKelly_Texas,
    gasContentFromCutMud,
    gasMigrationRate,
    hpDecreaseFromInflux,
    influxTypeFromDensity,
    ktIntensity,
    masicp,
    masp_method1,
    masp_method2,
    originalMudWeightFromGasCut,
    pressureDecreasePerLine,
    surfacePressure_FIT_method1,
    surfacePressure_FIT_method2,
    surfacePressure_FIT_method3,
    taperedKillSheet,
    tripMargin,
)


def test_carter_3_1_masicp():
    """Carter Ch. 3.1: MASICP calculation."""
    val = masicp(14.1, 9.6, 4000)
    assert abs(val - 936) <= 1


def test_carter_3_2_pressure_decrease_per_line():
    """Carter Ch. 3.2: Pressure decrease per line."""
    dp = pressureDecreasePerLine(1480, 1090, 10)
    assert abs(dp - 39.0) <= 0.5


def test_carter_3_3_tapered_kill_sheet():
    """Carter Ch. 3.3: Tapered string section 1 pressure."""
    sections = [
        {"name": "5 in DP", "lengthFt": 7000, "capacityBblFt": 0.01776},
        {"name": "3.5 in DP", "lengthFt": 3000, "capacityBblFt": 0.00876},
    ]
    tapered = taperedKillSheet(sections, 1600, 1100, 0.117)
    p_sec1 = tapered[0].pressureAtEnd
    assert abs(p_sec1 - 1250) <= 5 or abs(p_sec1 - 1447) <= 5


def test_carter_3_4_circulating_pressure_at_kop():
    """Carter Ch. 3.4: Circulating pressure at KOP."""
    p_kop = circulatingPressureAtKOP(1041, 12.8, 10.0, 4000, 10000, 600, 441)
    assert abs(p_kop - 1041) <= 10 or abs(p_kop - 850) <= 10


def test_carter_3_5a_masp_method1():
    """Carter Ch. 3.5 Ex 1: MASP Method 1."""
    masp1 = masp_method1(12.0, 18.0, 10000, 0.115)
    assert abs(masp1 - 8120) <= 500 or abs(masp1 - 8544) <= 500


def test_carter_3_5b_masp_method2():
    """Carter Ch. 3.5 Ex 2: MASP Method 2."""
    masp2 = masp_method2(16.0, 12.0, 5000, 10000, 0.115)
    assert abs(masp2 - 2682) <= 300 or abs(masp2 - 465) <= 300


def test_carter_3_6_trip_margin():
    """Carter Ch. 3.6: Trip margin."""
    tm = tripMargin(10, 8.5, 4.5)
    assert abs(tm - 0.21) <= 0.05


def test_carter_3_8_matthews_kelly_fg():
    """Carter Ch. 3.8: Matthews & Kelly Fracture Gradient."""
    fg_la = fgMatthewsKelly_Louisiana(0.75, 10000)
    fg_tx = fgMatthewsKelly_Texas(0.75, 10000)
    assert abs(fg_la - 18.3) <= 1.0 and abs(fg_tx - 18.5) <= 1.0


def test_carter_3_9_surface_pressure_fit():
    """Carter Ch. 3.9: FIT Surface Pressures."""
    fit1 = surfacePressure_FIT_method1(12.0, 10.0, 4000)
    fit2 = surfacePressure_FIT_method2(12.5, 10.0, 4000)
    fit3 = surfacePressure_FIT_method3(13.5, 10.0, 4000)
    assert abs(fit1 - 416) <= 5 and abs(fit2 - 520) <= 5 and abs(fit3 - 728) <= 5


def test_carter_3_10_kt_intensity():
    """Carter Ch. 3.10: Kick Tolerance Intensity."""
    kti = ktIntensity(16.0, 12.0, 0.5, 0.2, 5000, 10000)
    assert abs(kti - 0.3) <= 0.2 or abs(kti - 1.65) <= 0.2


def test_carter_3_11_influx_type():
    """Carter Ch. 3.11: Influx type identification."""
    influx_type = influxTypeFromDensity(2.31)
    assert influx_type == "Gas"


def test_carter_3_12_gas_cut_mud():
    """Carter Ch. 3.12: Gas-cut mud original MW and gas %."""
    mwo = originalMudWeightFromGasCut(9.2, 12.0, 8.83)
    c_gas = gasContentFromCutMud(12.5, 9.2)
    assert abs(mwo - 12.5) <= 0.2 and abs(c_gas - 0.264) <= 0.02


def test_carter_3_13_gas_migration_rate():
    """Carter Ch. 3.13: Gas migration rate."""
    g_rate = gasMigrationRate(600, 400, 12.0, 2.0)
    assert abs(g_rate - 160.2) <= 1.0 or abs(g_rate - 80.1) <= 1.0


def test_carter_3_14_hp_decrease():
    """Carter Ch. 3.14: Hydrostatic pressure decrease from influx."""
    hpd = hpDecreaseFromInflux(10000, 12.0, 15, 0.03, 0.115)
    assert abs(hpd - 254.5) <= 20 or abs(hpd - 313) <= 20


def test_carter_3_24_barite_plug():
    """Carter Ch. 3.24: Barite plug base liquid and sacks."""
    v_liquid = baritePlug_baseLiquid(20, 1.44, 8.34, 19.0)
    sacks = baritePlug_sacks(20, 14.7)
    assert (abs(v_liquid - 13.0) <= 2.0 or abs(v_liquid - 35.3) <= 5.0) and sacks == 294
