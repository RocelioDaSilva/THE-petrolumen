from __future__ import annotations

import base64
import io

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pandas as pd
from fastapi import APIRouter
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from pydantic import BaseModel

from ..engines.drilling.trajectory import compute_trajectory_minimum_curvature
from ..engines.geology.mesh import Grid3D
from ..engines.pvt.eos_solver import EosSolver
from ..engines.reservoir.nodal import find_operating_point, ipr_vogel, tpr
from .engine_routes import EosRequest, GridRequest, NodalRequest, SurveyInput

router = APIRouter()


class ChartResponse(BaseModel):
    image_base64: str
    content_type: str = "image/png"


def _encode_figure(fig) -> str:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=180, bbox_inches="tight")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    plt.close(fig)
    return encoded


@router.post("/engine/geology/grid/chart", tags=["Geology"], response_model=ChartResponse)
def chart_grid(payload: GridRequest) -> ChartResponse:
    """Return a chart of the grid extents and bulk volume."""
    x_span = float(payload.nx * (payload.dx[0] if isinstance(payload.dx, list) else payload.dx))
    y_span = float(payload.ny * (payload.dy[0] if isinstance(payload.dy, list) else payload.dy))
    z_span = float(payload.nz * (payload.dz[0] if isinstance(payload.dz, list) else payload.dz))

    fig = plt.figure(figsize=(6, 5))
    ax = fig.add_subplot(111, projection="3d")
    ax.bar3d(0, 0, 0, x_span, y_span, z_span, color="steelblue", alpha=0.7, edgecolor="navy")
    ax.set_title(f"Grid {payload.nx} x {payload.ny} x {payload.nz}")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.text2D(0.02, 0.98, f"cells={payload.nx * payload.ny * payload.nz}", transform=ax.transAxes, va="top")
    total_cells = payload.nx * payload.ny * payload.nz
    bulk_volume = float(np.sum(Grid3D(payload.nx, payload.ny, payload.nz, payload.dx, payload.dy, payload.dz).volumes))
    ax.text2D(0.02, 0.90, f"bulk_volume={bulk_volume:.2f}", transform=ax.transAxes, va="top")
    ax.view_init(elev=20, azim=35)
    fig.tight_layout()
    return ChartResponse(image_base64=_encode_figure(fig), content_type="image/png")


@router.post("/engine/pvt/eos/chart", tags=["PVT"], response_model=ChartResponse)
def chart_eos(payload: EosRequest) -> ChartResponse:
    """Plot the Z-factor curve for the requested EOS state."""
    solver = EosSolver(eos_type=payload.eos_type)
    for component in payload.components:
        properties = component.model_dump(exclude={"name", "molecular_weight"}, exclude_none=True)
        if component.molecular_weight is not None:
            properties["molecular_weight"] = component.molecular_weight
        solver.add_component(component.name, properties)

    count = len(payload.components)
    matrix = np.asarray(payload.binary_interactions if payload.binary_interactions is not None else np.zeros((count, count), dtype=float), dtype=float)
    solver.set_binary_interactions(matrix)

    pressures = np.linspace(0.5 * payload.pressure, 1.5 * payload.pressure, 50)
    z_values = []
    for pressure in pressures:
        z_values.append(float(solver.calculate_z_factor(pressure, payload.temperature, payload.composition)))

    target_z = float(solver.calculate_z_factor(payload.pressure, payload.temperature, payload.composition))

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(pressures / 1_000_000, z_values, color="tab:blue", linewidth=2, label="Z-factor")
    ax.scatter([payload.pressure / 1_000_000], [target_z], color="tab:red", s=70, zorder=5)
    ax.annotate(
        f"Z={target_z:.3f}",
        xy=(payload.pressure / 1_000_000, target_z),
        xytext=(8, 8),
        textcoords="offset points",
        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="gray", alpha=0.8),
    )
    ax.set_title(f"PVT EOS chart ({payload.eos_type})")
    ax.set_xlabel("Pressure (MPa)")
    ax.set_ylabel("Z-factor")
    ax.grid(alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    return ChartResponse(image_base64=_encode_figure(fig), content_type="image/png")


@router.post("/engine/reservoir/nodal/chart", tags=["Reservoir"], response_model=ChartResponse)
def chart_nodal(payload: NodalRequest) -> ChartResponse:
    """Return an IPR/TPR chart for the operating-point solution."""
    q_max = max(payload.qi * 1.4, 1.0)
    q_ipr = np.linspace(0.0, q_max, 120)
    p_wf_ipr = np.linspace(0.0, payload.pr * 0.98, len(q_ipr))
    q_ipr_vals = ipr_vogel(np.zeros_like(p_wf_ipr), payload.qi, payload.pr, p_wf_ipr)

    q_tpr = np.linspace(0.0, q_max, 120)
    p_wf_tpr = payload.p_surf + tpr(q_tpr, a=payload.a, b=payload.b)

    operating_rate = find_operating_point(payload.qi, payload.pr, payload.p_surf, payload.a, payload.b)
    operating_pwf = payload.p_surf + tpr(operating_rate, a=payload.a, b=payload.b)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(q_ipr_vals, p_wf_ipr, color="tab:blue", linewidth=2, label="IPR")
    ax.plot(q_tpr, p_wf_tpr, color="tab:orange", linewidth=2, label="TPR")
    ax.scatter([operating_rate], [operating_pwf], color="tab:red", s=70, zorder=5)
    ax.annotate(
        f"q_op={operating_rate:.2f}",
        xy=(operating_rate, operating_pwf),
        xytext=(8, 8),
        textcoords="offset points",
        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="gray", alpha=0.8),
    )
    ax.set_xlabel("Flow rate")
    ax.set_ylabel("Flowing bottom-hole pressure")
    ax.set_title("Nodal analysis IPR / TPR intersection")
    ax.grid(alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    return ChartResponse(image_base64=_encode_figure(fig), content_type="image/png")


@router.post("/engine/drilling/trajectory/chart", tags=["Drilling"], response_model=ChartResponse)
def chart_trajectory(payload: SurveyInput) -> ChartResponse:
    """Plot plan view and side view of a directional survey."""
    df = pd.DataFrame(payload.survey)
    result = compute_trajectory_minimum_curvature(
        df,
        md_col=payload.md_col,
        inc_col=payload.inc_col,
        azi_col=payload.azi_col,
    )

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    ax_plan, ax_side = axes

    plot_x = result["x"].to_numpy()
    plot_y = result["y"].to_numpy()
    plot_z = result["z"].to_numpy()

    ax_plan.plot(plot_x, plot_y, "o-", color="tab:green")
    for _, row in result.iterrows():
        ax_plan.annotate(str(round(float(row[payload.md_col]), 1)), (float(row["x"]), float(row["y"])), textcoords="offset points", xytext=(4, 4), fontsize=8)
    ax_plan.set_title("Plan view")
    ax_plan.set_xlabel("X")
    ax_plan.set_ylabel("Y")
    ax_plan.grid(alpha=0.25)

    ax_side.plot(plot_x, plot_z, "o-", color="tab:purple")
    for _, row in result.iterrows():
        ax_side.annotate(str(round(float(row[payload.md_col]), 1)), (float(row["x"]), float(row["z"])), textcoords="offset points", xytext=(4, 4), fontsize=8)
    ax_side.set_title("Side view")
    ax_side.set_xlabel("X")
    ax_side.set_ylabel("TVD")
    ax_side.grid(alpha=0.25)

    fig.suptitle("Directional well trajectory")
    return ChartResponse(image_base64=_encode_figure(fig), content_type="image/png")
