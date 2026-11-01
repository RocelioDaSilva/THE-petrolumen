"""Unit tests for newly modularized calculation engines and utilities."""

import numpy as np
import pandas as pd
import pytest

from app.utils.math_utils import deg2rad, min_curvature
from app.engines.drilling.ecd import pressure_from_density, hydrostatic_pressure_bar
from app.engines.drilling.driller_sim import simulate_driller_method
from app.engines.drilling.trajectory import compute_trajectory_minimum_curvature
from app.engines.reservoir.nodal import ipr_vogel, tpr, find_operating_point
from app.engines.reservoir.decline_curve import exponential, hyperbolic, harmonic
from app.engines.petrophysics.porosity import calculate_density_porosity
from app.engines.analytics.event_detection import detect_zscore


def test_math_utils():
    """Verify deg2rad and min_curvature trajectory computation."""
    rad = deg2rad(180.0)
    assert pytest.approx(rad, rel=1e-5) == np.pi

    md = [0, 100, 200]
    inc = [0, 10, 20]
    azi = [0, 45, 90]
    x, y, z = min_curvature(md, inc, azi)

    assert len(x) == 3
    assert len(y) == 3
    assert len(z) == 3
    assert x[0] == 0.0 and y[0] == 0.0 and z[0] == 0.0
    # Depth must increase downward
    assert z[1] > 0.0 and z[2] > z[1]


def test_ecd_pressure():
    """Verify hydrostatic pressure calculation from density and depth."""
    rho = 1200.0  # kg/m3
    depth = 3000.0  # m
    p_pa = pressure_from_density(rho, depth)
    p_bar = hydrostatic_pressure_bar(rho, depth)

    expected_pa = 1200.0 * 9.80665 * 3000.0
    assert pytest.approx(p_pa, rel=1e-5) == expected_pa
    assert pytest.approx(p_bar, rel=1e-5) == expected_pa / 1e5

    with pytest.raises(ValueError):
        pressure_from_density(-100, 1000)


def test_driller_sim():
    """Verify driller's method simulation produces expected trajectory."""
    df = simulate_driller_method(duration_hours=12.0, dt_min=10.0, initial_rop=15.0)

    assert isinstance(df, pd.DataFrame)
    assert "time_h" in df.columns
    assert "rop" in df.columns
    assert "md" in df.columns
    assert len(df) == 72
    assert df["md"].iloc[-1] > 0
    assert df["rop"].iloc[0] == 15.0
    # ROP should decay over time
    assert df["rop"].iloc[-1] < df["rop"].iloc[0]


def test_trajectory_minimum_curvature():
    """Verify DataFrame wrapper for trajectory calculation."""
    df_survey = pd.DataFrame({
        "md": [0.0, 500.0, 1000.0],
        "inc": [0.0, 15.0, 30.0],
        "azi": [0.0, 30.0, 60.0],
    })
    res = compute_trajectory_minimum_curvature(df_survey)

    assert "x" in res.columns
    assert "y" in res.columns
    assert "z" in res.columns
    assert res["z"].iloc[-1] > 0.0


def test_nodal_vogel_and_tpr():
    """Verify Vogel IPR, TPR, and operating point equilibrium."""
    qi = 5000.0
    pr = 3000.0
    # At pwf = pr, flow rate should be 0
    q_zero = ipr_vogel(0, qi, pr, pwf=pr)
    assert pytest.approx(q_zero, abs=1e-3) == 0.0

    # At pwf = 0, flow rate should be qi
    q_max = ipr_vogel(0, qi, pr, pwf=0.0)
    assert pytest.approx(q_max, abs=1e-3) == qi

    # Operating point should be between 0 and qi
    q_op = find_operating_point(qi=qi, pr=pr, p_surf=1000.0)
    assert 0 < q_op < qi


def test_decline_curves():
    """Verify exponential, hyperbolic, and harmonic Arps decline models."""
    t = np.array([0, 1, 2, 3])
    qi = 1000.0
    di = 0.1

    # At t = 0, all models must equal qi
    assert exponential(0, qi, di) == qi
    assert hyperbolic(0, qi, di, b=0.5) == qi
    assert harmonic(0, qi, di) == qi

    # Rates should decrease monotonically over time
    q_exp = exponential(t, qi, di)
    assert q_exp[1] < q_exp[0]
    assert q_exp[2] < q_exp[1]


def test_petrophysics_porosity():
    """Verify porosity calculation from bulk density."""
    phi = calculate_density_porosity(rho_bulk=2.50, rho_matrix=2.65, rho_fluid=1.0)
    expected_phi = (2.65 - 2.50) / (2.65 - 1.0)
    assert pytest.approx(phi, rel=1e-5) == expected_phi

    # Matrix density equal to bulk density yields 0 porosity
    phi_zero = calculate_density_porosity(rho_bulk=2.65, rho_matrix=2.65, rho_fluid=1.0)
    assert pytest.approx(phi_zero, abs=1e-6) == 0.0


def test_analytics_event_detection():
    """Verify rolling z-score event detection finds deliberate spike."""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=100, freq="min")
    values = np.ones(100) * 100.0
    # Insert an obvious outlier
    values[50] = 500.0
    df = pd.DataFrame({"pressure": values}, index=dates)

    anomalies = detect_zscore(df, "pressure", window=20, thresh=3.0)
    assert len(anomalies) > 0
    assert dates[50] in anomalies
