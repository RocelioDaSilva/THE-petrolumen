"""Regression tests for the ppes reservoir integration.

Locks the values verified end-to-end through the FastAPI layer so a future
ppes upgrade that changes a correlation constant fails loudly instead of
silently shifting production numbers.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.engines.reservoir.pvt import (
    pseudocritical_properties,
    calculate_z_factor_hall_yarborough,
    calculate_bubble_point_standing,
    calculate_oil_fvf_standing,
)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# pvt.py — direct tests (locked to current values; see pvt.py module docstring
# for why pseudocritical / z / Pb stay local rather than delegating to ppes).
# ---------------------------------------------------------------------------
def test_pvt_pseudocritical_gamma_065():
    assert pseudocritical_properties(0.65) == (670.13, 365.11)


def test_pvt_z_5000_180_065():
    assert calculate_z_factor_hall_yarborough(5000, 180, 0.65) == 0.9965


def test_pvt_bubble_point_500_35_180_065():
    assert calculate_bubble_point_standing(500, 0.65, 35, 180) == 2383.31


def test_pvt_bo_delegates_to_ppes_500_085_065_180():
    # After refactor this delegates to ppes_bridge.bo_standing; value is
    # identical to 4 dp to the old local implementation.
    assert calculate_oil_fvf_standing(500, 0.65, 0.85, 180) == 1.2672


# ---------------------------------------------------------------------------
# Chapter 2/3/8 endpoints — original batch
# ---------------------------------------------------------------------------
def test_health(client):
    assert client.get("/api/v1/reservoir/health").json() == {
        "status": "ok", "module": "reservoir", "engine": "ppes",
    }


def test_capabilities_original(client):
    mods = [m["name"] for m in
            client.get("/api/v1/reservoir/capabilities").json()["modules_exposed"]]
    assert mods == ["PVT", "IPR", "Decline"]


def test_vogel(client):
    r = client.post("/api/v1/reservoir/vogel",
                    json={"qmax": 978, "pwf": 2000, "pbar": 3000}).json()
    assert r["q"] == pytest.approx(499.86666666666673, abs=1e-9)
    assert r["method"] == "vogel_eq_3_19"


def test_vogel_pwf_gt_pbar_400(client):
    resp = client.post("/api/v1/reservoir/vogel",
                       json={"qmax": 978, "pwf": 3500, "pbar": 3000})
    assert resp.status_code == 400


def test_z_factor_endpoint(client):
    r = client.post("/api/v1/reservoir/z-factor",
                    json={"p": 5000, "t_F": 180, "gamma_g": 0.65}).json()
    assert r["z"] == pytest.approx(0.9917673885223415, abs=1e-9)
    assert r["p_pc"] == 671.4373
    assert r["t_pc"] == 370.26460000000003


def test_decline_exponential(client):
    r = client.post("/api/v1/reservoir/decline/exponential",
                    json={"qi": 100, "b": 0.04, "t": 12}).json()
    assert r["q"] == pytest.approx(61.878339180614084, abs=1e-9)
    assert r["cumulative"] == pytest.approx(953.0415204846479, abs=1e-9)


# ---------------------------------------------------------------------------
# Chapter 5/9/13 endpoints — second batch
# ---------------------------------------------------------------------------
def test_capabilities_ch5_9_13(client):
    chapters = [c["chapter"] for c in
                client.get("/api/v1/reservoir/capabilities/ch5-9-13")
                      .json()["chapters"]]
    assert chapters == [5, 9, 13]


def test_health_ch5_9_13(client):
    assert client.get("/api/v1/reservoir/health/ch5-9-13").json() == {
        "status": "ok", "chapters": [5, 9, 13], "engine": "ppes",
    }


def test_gilbert_choke(client):
    r = client.post("/api/v1/reservoir/choke/gilbert",
                    json={"q_bpd": 1000, "glr": 500, "choke_64": 24}).json()
    # Field is now `p_wh`, not `result` (see gilbert docstring: Eq. 5.12 [psia]).
    assert r["p_wh"] == pytest.approx(732.8892905222332, abs=1e-9)
    assert r["method"] == "gilbert_eq_5_12"
    assert "result" not in r


def test_critical_ratio(client):
    r = client.post("/api/v1/reservoir/choke/critical-ratio",
                    json={"k": 1.28}).json()
    assert r["critical_ratio"] == pytest.approx(0.5493682252115829, abs=1e-9)


def test_collapse_biaxial(client):
    r = client.post("/api/v1/reservoir/tubing/collapse-biaxial",
                    json={"p_c": 5000, "sa": 20000, "ym": 80000}).json()
    assert r["p_collapse_adjusted"] == pytest.approx(4256.406047441658, abs=1e-9)


def test_valve_depth(client):
    r = client.post("/api/v1/reservoir/gas-lift/valve-depth",
                    json={"pk_s": 500, "dp_km": 100, "phf": 200,
                          "Gs": 0.1}).json()
    assert r["depth"] == pytest.approx(2222.222222222222, abs=1e-9)


def test_orifice_size(client):
    r = client.post("/api/v1/reservoir/gas-lift/orifice-size",
                    json={"q_mscfd": 500, "p_up": 800, "p_dn": 200,
                          "gg": 0.65, "t_R": 600}).json()
    assert r["area_in2"] == pytest.approx(0.035265597640286625, abs=1e-12)
    assert r["diameter_in"] == pytest.approx(0.21190377888500403, abs=1e-12)


def test_orifice_pdn_gt_pup_400(client):
    resp = client.post("/api/v1/reservoir/gas-lift/orifice-size",
                       json={"q_mscfd": 500, "p_up": 200, "p_dn": 800,
                             "gg": 0.65, "t_R": 600})
    assert resp.status_code == 400
# ---------------------------------------------------------------------------
# Chapter 2 PVT endpoints — appended
# ---------------------------------------------------------------------------
def test_capabilities_pvt(client):
    n = len(client.get("/api/v1/reservoir/capabilities/pvt").json()["endpoints"])
    assert n == 13


def test_health_pvt(client):
    assert client.get("/api/v1/reservoir/health/pvt").json() == {
        "status": "ok", "chapter": 2, "engine": "ppes",
    }


def test_pvt_rs_standing(client):
    r = client.post("/api/v1/reservoir/pvt/rs-standing",
                    json={"p": 2383.31, "t_F": 180, "api": 35,
                          "gamma_g": 0.65}).json()
    assert r["rs"] == pytest.approx(500.1979544225763, abs=1e-9)


def test_pvt_bo_standing(client):
    r = client.post("/api/v1/reservoir/pvt/bo-standing",
                    json={"t_F": 180, "api": 35, "rs": 500,
                          "gamma_g": 0.65}).json()
    assert r["bo"] == pytest.approx(1.2672587189945002, abs=1e-9)


def test_pvt_mu_dead_oil(client):
    r = client.post("/api/v1/reservoir/pvt/mu-dead-oil",
                    json={"api": 35, "t_F": 180}).json()
    assert r["mu_od"] == pytest.approx(1.6656214956472237, abs=1e-9)


def test_pvt_rho_oil(client):
    r = client.post("/api/v1/reservoir/pvt/rho-oil",
                    json={"p": 2000, "t_F": 180, "api": 35, "rs": 500,
                          "gamma_g": 0.65}).json()
    assert r["rho_o"] == pytest.approx(45.04462975199444, abs=1e-9)


def test_pvt_rho_gas(client):
    r = client.post("/api/v1/reservoir/pvt/rho-gas",
                    json={"p": 2000, "t_R": 640, "gamma_g": 0.65,
                          "z": 0.9}).json()
    assert r["rho_g"] == pytest.approx(6.093750000000001, abs=1e-9)


def test_pvt_bg(client):
    r = client.post("/api/v1/reservoir/pvt/bg",
                    json={"p": 2000, "t_R": 640, "z": 0.9}).json()
    assert r["bg"] == pytest.approx(0.008150399999999999, abs=1e-12)


def test_pvt_eg(client):
    r = client.post("/api/v1/reservoir/pvt/eg",
                    json={"p": 2000, "t_R": 640, "z": 0.9}).json()
    assert r["eg"] == pytest.approx(122.56944444444444, abs=1e-9)
    # NOTE: not exactly 1/bg — book defines Eg independently; 0.1% drift.


def test_pvt_oil_compressibility(client):
    r = client.post("/api/v1/reservoir/pvt/oil-compressibility",
                    json={"p": 2000, "rs": 500, "t_F": 180, "api": 35,
                          "gamma_g": 0.65}).json()
    assert r["co"] == pytest.approx(1.918675e-06, abs=1e-12)


def test_pvt_z_brill_beggs(client):
    r = client.post("/api/v1/reservoir/pvt/z-brill-beggs",
                    json={"p": 5000, "t_F": 180, "gamma_g": 0.65}).json()
    assert r["z"] == pytest.approx(0.9714646592553121, abs=1e-9)
    assert r["method"] == "z_brill_beggs"


# Previously smoke-tested, now exact-locked with the values from the
# 2026-11-04 verify run. See docstrings for the physical sanity checks.
def test_pvt_mu_sat_oil(client):
    r = client.post("/api/v1/reservoir/pvt/mu-sat-oil",
                    json={"rs": 500, "mu_od": 1.67}).json()
    # Saturated oil viscosity must be LESS than dead oil (gas dissolves,
    # oil thins). 0.6887 < 1.67 — correct direction.
    assert r["mu_ob"] == pytest.approx(0.6886806229189156, abs=1e-9)
    assert r["mu_ob"] < 1.67


def test_pvt_mu_unsat_oil(client):
    r = client.post("/api/v1/reservoir/pvt/mu-unsat-oil",
                    json={"p": 3000, "pb": 2383.31, "mu_od": 1.67,
                          "mu_ob": 1.0}).json()
    # Undersaturated above pb: viscosity > mu_ob.
    assert r["mu_o"] == pytest.approx(1.2679642741556578, abs=1e-9)
    assert r["mu_o"] > 1.0


def test_pvt_mu_gas_low_pressure(client):
    r = client.post("/api/v1/reservoir/pvt/mu-gas-low-pressure",
                    json={"gamma_g": 0.65, "t_R": 640}).json()
    assert r["mu_g"] == pytest.approx(0.01941839085664644, abs=1e-12)


def test_pvt_wichert_aziz(client):
    # W-A sour-gas correction returns (p_pc_corrected, t_pc_corrected).
    # Both should be BELOW the uncorrected inputs (671.44, 370.26).
    r = client.post("/api/v1/reservoir/pvt/wichert-aziz",
                    json={"y_H2S": 0.02, "y_CO2": 0.01,
                          "p_pc": 671.44, "t_pc": 370.26}).json()
    assert r["p_pc_corrected"] == pytest.approx(658.8822327854112, abs=1e-9)
    assert r["t_pc_corrected"] == pytest.approx(363.465799534422, abs=1e-9)
    assert r["p_pc_corrected"] < 671.44
    assert r["t_pc_corrected"] < 370.26
# ---------------------------------------------------------------------------
# Ch 5/9/13 endpoints that had no tests — exact-lock from the 2026-11-04 run.
# ---------------------------------------------------------------------------
def test_choke_sonic_gas(client):
    r = client.post("/api/v1/reservoir/choke/sonic-gas",
                    json={"cd": 0.85, "A2_in2": 0.05, "p_up": 800,
                          "t_up_R": 600, "gamma_g": 0.65,
                          "k": 1.28}).json()
    assert r["q_mscfd"] == pytest.approx(1004.2837506376885, abs=1e-9)


def test_choke_subsonic_gas(client):
    r = client.post("/api/v1/reservoir/choke/subsonic-gas",
                    json={"cd": 0.85, "A2_in2": 0.05, "p_up": 800,
                          "p_dn": 600, "t_up_R": 600, "gamma_g": 0.65,
                          "k": 1.28}).json()
    assert r["q_mscfd"] == pytest.approx(906.175786455616, abs=1e-9)


def test_choke_subsonic_lt_sonic(client):
    # Physical constraint: same geometry/p_up, subsonic flow < sonic flow.
    # Protects against a regression that would flip the branch selection.
    payload_s = {"cd": 0.85, "A2_in2": 0.05, "p_up": 800,
                 "t_up_R": 600, "gamma_g": 0.65, "k": 1.28}
    payload_sub = dict(payload_s, p_dn=600)
    q_s = client.post("/api/v1/reservoir/choke/sonic-gas",
                      json=payload_s).json()["q_mscfd"]
    q_sub = client.post("/api/v1/reservoir/choke/subsonic-gas",
                        json=payload_sub).json()["q_mscfd"]
    assert q_sub < q_s


def test_tubing_ballooning(client):
    r = client.post("/api/v1/reservoir/tubing/ballooning",
                    json={"dpi": 2000, "dpo": 0, "A_i": 4.43,
                          "A_o": 6.66, "L": 10000}).json()
    assert r["delta_L"] == pytest.approx(0.7946188340807174, abs=1e-9)


def test_tubing_piston(client):
    r = client.post("/api/v1/reservoir/tubing/piston",
                    json={"pi_c": 2000, "po_c": 1000, "A_p": 4.43,
                          "A_i": 4.43, "A_o": 6.66, "L": 10000,
                          "E": 30000000, "A_s": 2.23}).json()
    # Endpoint unpacks (F, dL); F = (pi_c-po_c)*A_s = 1000*2.23 = 2230 lbf.
    assert r["force_lbf"] == pytest.approx(2230.0000000000005, abs=1e-9)
    assert r["delta_L_ft"] == pytest.approx(0.33333333333333337, abs=1e-9)


def test_tubing_bending_stress(client):
    r = client.post("/api/v1/reservoir/tubing/bending-stress",
                    json={"E": 30000000, "Do": 2.875,
                          "Rc": 1000}).json()
    # Exact: E*Do/(2*Rc) = 3e7*2.875/(2*1000) = 43125 psi.
    assert r["stress"] == pytest.approx(43125.0, abs=1e-9)


def test_gas_lift_valve_open_close(client):
    r = client.post("/api/v1/reservoir/gas-lift/valve-open-close",
                    json={"pd": 800, "St": 0, "R": 0.1,
                          "pt": 400}).json()
    # Physical: opening pressure > closing pressure. With St=0, closing = pd.
    assert r["p_open"] == pytest.approx(844.4444444444445, abs=1e-9)
    assert r["p_close"] == pytest.approx(800.0, abs=1e-9)
    assert r["p_open"] > r["p_close"]


def test_gas_lift_injection_glr(client):
    r = client.post("/api/v1/reservoir/gas-lift/injection-glr",
                    json={"glr_opt": 800, "glr_form": 300}).json()
    # Exact: glr_inj = glr_opt - glr_form = 500.
    assert r["glr_inj"] == pytest.approx(500.0, abs=1e-9)