"""Golden-style validation for the consolidated well-test analysis engine.

The drawdown/buildup recoveries are generated from the infinite-acting
line-source solution, so the analyzer should return the input permeability
and skin exactly (within floating-point tolerance).
"""

from __future__ import annotations

import numpy as np
import pytest

from app.engines.reservoir.well_test_analysis import (
    analyze_buildup,
    analyze_drawdown,
    bourdet_derivative,
)

# --- Reservoir / fluid model used by every test ---------------------------
K = 50.0        # mD
H = 30.0        # ft
Q = 500.0       # STB/d
B = 1.2         # RB/STB
MU = 1.0        # cp
PHI = 0.2       # fraction
CT = 1.0e-5     # 1/psi
RW = 0.3        # ft
PI = 4000.0     # psia
SKIN = 2.0


def _line_source_drawdown(t_hours, skin=SKIN):
    """p_wf(t) for constant-rate drawdown in an infinite-acting reservoir."""
    m = -162.6 * Q * B * MU / (K * H)  # psi/cycle (negative)
    d = K / (PHI * MU * CT * RW ** 2)
    return PI + m * (np.log10(t_hours) + np.log10(d) - 3.2275 + 0.8686 * skin)


def _horner_buildup(dt_hours, tp_hours, skin=SKIN):
    """p_ws(dt) for a Horner buildup."""
    m_abs = 162.6 * Q * B * MU / (K * H)
    p_wf0 = PI - m_abs * (np.log10(tp_hours) + np.log10(K / (PHI * MU * CT * RW ** 2)) - 3.2275 + 0.8686 * skin)
    return PI - m_abs * np.log10((tp_hours + dt_hours) / dt_hours), p_wf0


def test_drawdown_recovers_permeability_and_skin():
    t = np.logspace(0, 2.3, 60)  # 1 .. ~200 hours
    p = _line_source_drawdown(t)

    result = analyze_drawdown(
        time=t,
        pressure=p,
        rate=Q,
        viscosity=MU,
        total_compressibility=CT,
        porosity=PHI,
        wellbore_radius=RW,
        initial_pressure=PI,
        net_pay=H,
        formation_volume_factor=B,
    )

    assert result.permeability_md == pytest.approx(K, rel=1e-2)
    assert result.skin == pytest.approx(SKIN, abs=0.05)
    assert result.slope_psi_per_cycle < 0  # drawdown slope is negative
    assert result.regimes.radial is not None


def test_buildup_recovers_permeability_and_skin():
    tp = 1000.0  # hours producing before shut-in
    dt = np.logspace(0, 2, 60)  # 1 .. 100 hours shut-in
    p, p_wf0 = _horner_buildup(dt, tp)

    result = analyze_buildup(
        time=dt,
        pressure=p,
        rate=Q,
        viscosity=MU,
        total_compressibility=CT,
        porosity=PHI,
        wellbore_radius=RW,
        producing_time=tp,
        p_wf_at_shutin=p_wf0,
        net_pay=H,
        formation_volume_factor=B,
    )

    assert result.permeability_md == pytest.approx(K, rel=1e-2)
    assert result.skin == pytest.approx(SKIN, abs=0.05)
    assert result.p_star_psi == pytest.approx(PI, abs=0.5)


def test_bourdet_derivative_interior_is_finite():
    t = np.logspace(0, 2.3, 60)
    p = _line_source_drawdown(t)
    d = bourdet_derivative(t, p)
    assert np.all(np.isfinite(d[1:-1]))
    # Bourdet derivative is dP/d(ln t); radial-flow value is m/ln(10) (~ -28.25).
    m_cycle = -162.6 * Q * B * MU / (K * H)
    assert np.nanmean(d[1:-1]) == pytest.approx(m_cycle / np.log(10), rel=0.05)


@pytest.mark.parametrize(
    "bad_time,bad_pressure",
    [
        (np.array([1.0, 2.0]), np.array([3000.0, 3000.0, 3000.0])),  # length mismatch
        (np.array([1.0, 2.0, 2.0]), np.array([3000.0, 3000.0, 3000.0])),  # not increasing
        (np.array([0.0, 1.0, 2.0]), np.array([3000.0, 3000.0, 3000.0])),  # t <= 0
        (np.array([1.0, 2.0, 3.0]), np.array([3000.0, np.nan, 3000.0])),  # NaN pressure
    ],
)
def test_invalid_input_raises(bad_time, bad_pressure):
    with pytest.raises(ValueError):
        analyze_drawdown(
            time=bad_time,
            pressure=bad_pressure,
            rate=Q,
            viscosity=MU,
            total_compressibility=CT,
            porosity=PHI,
            wellbore_radius=RW,
            initial_pressure=PI,
            net_pay=H,
        )


def test_negative_rate_raises():
    t = np.logspace(0, 2, 20)
    p = _line_source_drawdown(t)
    with pytest.raises(ValueError):
        analyze_drawdown(
            time=t, pressure=p, rate=-Q, viscosity=MU, total_compressibility=CT,
            porosity=PHI, wellbore_radius=RW, initial_pressure=PI, net_pay=H,
        )
