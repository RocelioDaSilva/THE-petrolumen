"""Unit tests for newly modularized calculation engines and utilities."""

import numpy as np
import pandas as pd
import pytest
from app.engines.analytics.event_detection import detect_zscore
from app.engines.analytics.sequences import create_sequences, normalize_timeseries
from app.engines.drilling.driller_sim import simulate_driller_method
from app.engines.drilling.ecd import hydrostatic_pressure_bar, pressure_from_density
from app.engines.drilling.rop import (
    cuttings_concentration,
    d_exponent,
    predict_rop,
    rop_mud_effects,
    train_rop_model,
)
from app.engines.drilling.trajectory import compute_trajectory_minimum_curvature
from app.engines.petrophysics.facies import predict_facies, train_facies_classifier
from app.engines.petrophysics.porosity import calculate_density_porosity
from app.engines.reservoir.decline_curve import exponential, harmonic, hyperbolic
from app.engines.reservoir.material_balance import (
    calculate_fmb_gas,
    estimate_ogip_from_production,
)
from app.engines.reservoir.nodal import find_operating_point, ipr_vogel
from app.engines.reservoir.pvt import (
    calculate_bubble_point_standing,
    calculate_oil_fvf_standing,
    calculate_z_factor_hall_yarborough,
    pseudocritical_properties,
)
from app.utils.math_utils import deg2rad, min_curvature


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

    # Incompatible density raises ValueError
    with pytest.raises(ValueError):
        calculate_density_porosity(rho_bulk=2.5, rho_matrix=1.0, rho_fluid=1.0)


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


# =========================================================================
# Newly Modularized Engine Tests
# =========================================================================

def test_facies_classification_engine():
    """Verify facies classification training and inference."""
    data = {
        "gamma": [80.0, 75.0, 200.0, 150.0, 90.0, 85.0],
        "resistivity": [200.0, 220.0, 5.0, 10.0, 150.0, 180.0],
        "density": [2.58, 2.60, 2.30, 2.45, 2.55, 2.57],
        "porosity": [0.12, 0.10, 0.28, 0.22, 0.15, 0.13],
        "facies": [1, 1, 3, 2, 1, 1],
    }
    df = pd.DataFrame(data)

    clf, report, preds = train_facies_classifier(df, target_col="facies", n_estimators=50)
    assert clf is not None
    assert isinstance(report, dict)
    assert len(preds) > 0

    # Predict on unseen row
    new_data = pd.DataFrame({
        "gamma": [78.0],
        "resistivity": [210.0],
        "density": [2.59],
        "porosity": [0.11],
    })
    pred_class = predict_facies(clf, new_data)
    assert len(pred_class) == 1
    assert pred_class[0] in [1, 2, 3]

    # Empty DataFrame must raise ValueError
    with pytest.raises(ValueError):
        train_facies_classifier(pd.DataFrame())

    # Missing features must raise ValueError
    with pytest.raises(ValueError):
        predict_facies(clf, pd.DataFrame({"gamma": [100.0]}))


def test_rop_physics_and_modeling():
    """Verify ROP equations and ML regression engine."""
    # Carter ROP mud effects
    rop_adj = rop_mud_effects(rop1_ft_hr=20.0, mw1_ppg=10.0, mw2_ppg=12.0)
    expected_rop = 20.0 * ((10.0 / 12.0) ** 2)
    assert pytest.approx(rop_adj, abs=0.1) == expected_rop

    # Cuttings concentration
    ca = cuttings_concentration(rop_ft_hr=30.0, bit_diameter_in=8.5, flow_rate_gpm=450.0)
    assert 0.0 < ca < 20.0

    # Jordan & Shirley d-exponent
    d_exp, dc = d_exponent(rop_ft_hr=40.0, rpm=120.0, wob_klbs=25.0, bit_diameter_in=8.5, mw_actual_ppg=10.0)
    assert d_exp > 0.0
    assert dc > 0.0

    # ML ROP regression model
    df_rop = pd.DataFrame({
        "WOB": [10000.0, 11000.0, 10500.0, 11500.0, 12000.0, 9000.0],
        "RPM": [120.0, 125.0, 123.0, 128.0, 130.0, 110.0],
        "torque": [5.0, 5.5, 5.2, 5.6, 6.0, 4.5],
        "mud_weight": [1200.0, 1200.0, 1200.0, 1200.0, 1200.0, 1200.0],
        "ROP": [5.0, 5.5, 5.1, 5.7, 6.2, 4.8],
    })
    model, metrics, _preds = train_rop_model(df_rop, n_estimators=50)
    assert model is not None
    assert "rmse" in metrics and "mae" in metrics
    assert metrics["rmse"] >= 0.0

    test_pred = predict_rop(model, df_rop.iloc[[0]])
    assert len(test_pred) == 1
    assert test_pred[0] > 0.0

    # Error handling on invalid values
    with pytest.raises(ValueError):
        rop_mud_effects(20.0, -9.0, 10.0)
    with pytest.raises(ValueError):
        d_exponent(-10.0, 100.0, 20.0, 8.5)


def test_time_series_sequences_and_normalization():
    """Verify time series sliding sequence generator and normalization."""
    raw = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0]
    norm, mean, _std = normalize_timeseries(raw)
    assert pytest.approx(mean, abs=1e-5) == 45.0
    assert pytest.approx(np.mean(norm), abs=1e-5) == 0.0
    assert pytest.approx(np.std(norm), abs=1e-5) == 1.0

    # Sliding window sequences
    x_seq, y_seq = create_sequences(norm, window=3, horizon=1)
    assert x_seq.shape == (5, 3)
    assert len(y_seq) == 5
    assert np.allclose(x_seq[0], norm[0:3])
    assert pytest.approx(y_seq[0]) == norm[3]

    # Boundary conditions
    with pytest.raises(ValueError):
        create_sequences([], window=3)
    with pytest.raises(ValueError):
        create_sequences([1, 2], window=5)
    with pytest.raises(ValueError):
        create_sequences([1, 2, 3], window=0)


def test_pvt_correlations():
    """Verify thermodynamic PVT calculations (Hall-Yarborough Z, Sutton, Standing)."""
    # Sutton pseudocritical properties
    ppc, tpc = pseudocritical_properties(gamma_g=0.65)
    assert 600.0 < ppc < 750.0
    assert 300.0 < tpc < 450.0

    # Hall-Yarborough Z-factor
    z = calculate_z_factor_hall_yarborough(pressure_psia=3000.0, temperature_f=160.0, gamma_g=0.65)
    assert 0.6 < z < 1.2

    # Standing bubble point
    pb = calculate_bubble_point_standing(rs_scf_stb=500.0, gamma_g=0.7, api=35.0, temperature_f=180.0)
    assert pb > 1000.0

    # Standing oil formation volume factor Bo
    bo = calculate_oil_fvf_standing(rs_scf_stb=500.0, gamma_g=0.7, gamma_o=0.85, temperature_f=180.0)
    assert 1.0 < bo < 2.0

    # Invalid negative inputs must fail loudly
    with pytest.raises(ValueError):
        calculate_z_factor_hall_yarborough(pressure_psia=-500.0, temperature_f=100.0, gamma_g=0.65)
    with pytest.raises(ValueError):
        pseudocritical_properties(gamma_g=-0.5)


def test_gas_material_balance():
    """Verify Flowing Material Balance (FMB) straight-line OGIP method."""
    fmb = calculate_fmb_gas(pi=3200.0, tf=160.0, gamma_g=0.65, ogip_expected=1200.0, steps=10)
    assert fmb["ogip"] == 1200.0
    assert fmb["slope"] < 0.0
    assert len(fmb["points"]) == 11
    assert fmb["points"][0]["gp"] == 0.0
    assert fmb["points"][-1]["pz"] < fmb["points"][0]["pz"]

    # Linear regression estimation of OGIP from synthetic decline
    gp_data = [pt["gp"] for pt in fmb["points"]]
    pz_data = [pt["pz"] for pt in fmb["points"]]
    ogip_est, slope_est, _pzi_est = estimate_ogip_from_production(gp_data, pz_data)

    assert pytest.approx(ogip_est, rel=1e-2) == 1200.0
    assert slope_est < 0.0

    # Invalid cases
    with pytest.raises(ValueError):
        calculate_fmb_gas(pi=-100.0)
    with pytest.raises(ValueError):
        estimate_ogip_from_production([10.0], [3000.0])  # Only 1 point


def test_edge_cases_and_error_handling():
    """Verify edge-case boundaries, zero division guards, and exception handling."""
    from app.engines.drilling.well_control import (
        barite_plug_base_liquid,
        diverter_line_diameter,
        influx_length,
        influx_length_multi_section,
        kt_influx_length,
        trip_margin,
    )

    # 1. Decline curves edge cases
    with pytest.raises(ValueError):
        exponential(t=-1.0, qi=100.0, di=0.1)
    with pytest.raises(ValueError):
        hyperbolic(t=1.0, qi=-10.0, di=0.1, b=0.5)
    with pytest.raises(ValueError):
        hyperbolic(t=1.0, qi=100.0, di=0.1, b=-0.5)
    with pytest.raises(ValueError):
        harmonic(t=1.0, qi=100.0, di=-0.2)
    # b = 0 should reduce to exponential
    assert hyperbolic(5.0, 1000.0, 0.05, b=0) == exponential(5.0, 1000.0, 0.05)

    # 2. Nodal operating point edge cases
    with pytest.raises(ValueError):
        # Surface backpressure >= reservoir pressure
        find_operating_point(qi=1000.0, pr=2000.0, p_surf=2500.0)
    with pytest.raises(ValueError):
        # Negative max rate
        find_operating_point(qi=-1000.0, pr=2000.0, p_surf=500.0)
    with pytest.raises(ValueError):
        # Negative bottomhole pressure in Vogel
        ipr_vogel(0, 1000.0, 3000.0, pwf=-100.0)

    # 3. PVT edge cases
    with pytest.raises(ValueError):
        # Temperature below absolute zero
        calculate_z_factor_hall_yarborough(1000.0, -500.0, 0.65)
    with pytest.raises(ValueError):
        # Non-physical negative GOR
        calculate_bubble_point_standing(rs_scf_stb=-10.0, gamma_g=0.65, api=30.0, temperature_f=150.0)
    with pytest.raises(ValueError):
        # Negative oil gravity
        calculate_oil_fvf_standing(rs_scf_stb=200.0, gamma_g=0.65, gamma_o=-0.8, temperature_f=150.0)

    # 4. Petrophysics porosity boundaries
    with pytest.raises(ValueError):
        calculate_density_porosity(rho_bulk=-1.5)
    with pytest.raises(ValueError):
        calculate_density_porosity(rho_bulk=2.5, rho_matrix=0.0)

    # 5. Math utils & trajectory
    with pytest.raises(ValueError):
        min_curvature([], [], [])
    with pytest.raises(ValueError):
        min_curvature([0, 100], [0], [0])

    # 6. Well control edge cases
    with pytest.raises(ValueError):
        trip_margin(yp=15.0, dh_inches=8.5, dp_inches=8.5)  # dh == dp
    with pytest.raises(ValueError):
        diverter_line_diameter(dh_inches=5.0, dp_inches=6.0)  # dh < dp
    with pytest.raises(ValueError):
        kt_influx_length(masicp_psi=500.0, g_mud_psi_ft=0.5, g_influx_psi_ft=0.5)  # identical gradients
    with pytest.raises(ValueError):
        influx_length(v_kick_bbl=20.0, ca_bbl_ft=0.0)  # zero capacity
    with pytest.raises(ValueError):
        influx_length_multi_section(v_kick_bbl=20.0, c_dc_oh_bbl_ft=0.0, l_dc_ft=100.0, c_dp_oh_bbl_ft=0.05)
    with pytest.raises(ValueError):
        barite_plug_base_liquid(v_plug_bbl=50.0, w_mud_sg=1.2, mw_liquid_ppg=12.0, mw_plug_ppg=12.0)

    # 7. Driller sim edge cases
    with pytest.raises(ValueError):
        simulate_driller_method(initial_rop=-5.0)
    with pytest.raises(ValueError):
        simulate_driller_method(decay_constant_hours=-10.0)

    # 8. Analytics event detection edge cases
    with pytest.raises(ValueError):
        detect_zscore(pd.DataFrame(), "col")
    with pytest.raises(ValueError):
        detect_zscore(pd.DataFrame({"col": [1, 2, 3]}), "missing")
    with pytest.raises(ValueError):
        detect_zscore(pd.DataFrame({"col": [1, 2, 3]}), "col", window=0)
