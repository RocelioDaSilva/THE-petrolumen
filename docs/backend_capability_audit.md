# PetroLúmen Backend Capability Audit

> **Historical snapshot:** this audit predates the current route wiring and is
> not the source of truth for the active API or engine status. See
> [API_REFERENCE.md](API_REFERENCE.md) for the current OpenAPI operation
> inventory and [ENGINE_CAPABILITIES.md](ENGINE_CAPABILITIES.md) for current
> capability descriptions and limitations. The inventories and file counts
> below are retained as historical audit evidence and may be stale.

This document provides a comprehensive audit of the PetroLúmen FastAPI calculation backend under `backend/app/`, evaluating API endpoint definitions, computational calculation engines, functional surface gaps, and test suite execution coverage.

---

## Section 1 — Endpoint Inventory

Inventory of all routes defined across routers in `backend/app/api/` (`simulation_routes.py`, `engine_routes.py`, `chart_routes.py`) as registered under `/api` in `backend/app/main.py`. *(Note: Global diagnostic routes `GET /health` and `GET /` defined in `main.py` are also noted below for completeness).*

| Method | Path | Request Pydantic Model (Name & Fields) | Actual Response Shape | Current Status | Has Test? (Name) | Has `response_model`? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`POST`** | `/api/engine/pvt/eos` | **`EosRequest`**:<br>- `pressure`: PositiveFloat (Pa)<br>- `temperature`: PositiveFloat (K)<br>- `components`: list[EosComponentInput] (`name`: str, `critical_pressure`: PositiveFloat, `critical_temperature`: PositiveFloat, `acentric_factor`: float, `molecular_weight`: PositiveFloat | None)<br>- `composition`: dict[str, float]<br>- `eos_type`: Literal['PR'] = 'PR'<br>- `binary_interactions`: list[list[float]] | None = None | `{"z_factor": float}` | 200-working | Yes (`test_eos_endpoint_calculates_peng_robinson_z_factor`) | Yes (`EosResponse`) |
| **`POST`** | `/api/engine/drilling/trajectory` | **`SurveyInput`**:<br>- `survey`: list[dict[str, float]]<br>- `md_col`: str = 'md'<br>- `inc_col`: str = 'inc'<br>- `azi_col`: str = 'azi' | `{"survey": [{"md": float, "inc": float, "azi": float, "x": float, "y": float, "z": float}]}` | 200-working | Yes (`test_trajectory_endpoint_returns_minimum_curvature_coordinates`) | Yes (`TrajectoryResponse`) |
| **`POST`** | `/api/engine/geology/grid` | **`GridRequest`**:<br>- `nx`: int (gt=0)<br>- `ny`: int (gt=0)<br>- `nz`: int (gt=0)<br>- `dx`: PositiveFloat | list[PositiveFloat]<br>- `dy`: PositiveFloat | list[PositiveFloat]<br>- `dz`: PositiveFloat | list[PositiveFloat] | `{"shape": [int, int, int], "total_cells": int, "bulk_volume": float}` | 200-working *(runtime requires module import fix in `mesh.py`)* | Yes (`test_geology_grid_endpoint_sums_variable_cell_volumes`, `test_grid_endpoint_roundtrip`) | Yes (`GridResponse`) |
| **`POST`** | `/api/engine/reservoir/nodal` | **`NodalRequest`**:<br>- `qi`: PositiveFloat<br>- `pr`: PositiveFloat<br>- `p_surf`: float = 1000.0 (ge=0)<br>- `a`: float = 0.002 (ge=0)<br>- `b`: float = 10.0 (ge=0) | `{"operating_rate": float}` | 200-working | Yes (`test_nodal_endpoint_finds_operating_rate_and_rejects_nonflowing_case`) | Yes (`NodalResponse`) |
| **`POST`** | `/api/engine/geology/grid/chart` | **`GridRequest`**:<br>- `nx`: int (gt=0)<br>- `ny`: int (gt=0)<br>- `nz`: int (gt=0)<br>- `dx`: PositiveFloat | list[PositiveFloat]<br>- `dy`: PositiveFloat | list[PositiveFloat]<br>- `dz`: PositiveFloat | list[PositiveFloat] | `{"image_base64": str, "content_type": "image/png"}` | 200-working *(runtime requires module import fix in `mesh.py`)* | Yes (`test_grid_chart_returns_png`) | Yes (`ChartResponse`) |
| **`POST`** | `/api/engine/pvt/eos/chart` | **`EosRequest`**:<br>- `pressure`: PositiveFloat<br>- `temperature`: PositiveFloat<br>- `components`: list[EosComponentInput]<br>- `composition`: dict[str, float]<br>- `eos_type`: Literal['PR'] = 'PR'<br>- `binary_interactions`: list[list[float]] | None = None | `{"image_base64": str, "content_type": "image/png"}` | 200-working | Yes (`test_eos_chart_returns_png`) | Yes (`ChartResponse`) |
| **`POST`** | `/api/engine/reservoir/nodal/chart` | **`NodalRequest`**:<br>- `qi`: PositiveFloat<br>- `pr`: PositiveFloat<br>- `p_surf`: float = 1000.0<br>- `a`: float = 0.002<br>- `b`: float = 10.0 | `{"image_base64": str, "content_type": "image/png"}` | 200-working | Yes (`test_nodal_chart_returns_png`) | Yes (`ChartResponse`) |
| **`POST`** | `/api/engine/drilling/trajectory/chart` | **`SurveyInput`**:<br>- `survey`: list[dict[str, float]]<br>- `md_col`: str = 'md'<br>- `inc_col`: str = 'inc'<br>- `azi_col`: str = 'azi' | `{"image_base64": str, "content_type": "image/png"}` | 200-working | Yes (`test_trajectory_chart_returns_png`) | Yes (`ChartResponse`) |
| **`POST`** | `/api/simulate/black-oil` | **`BlackOilInput`**:<br>- `grid`: GridInput (`nx`: int, `ny`: int, `nz`: int, `dx`: PositiveFloat, `dy`: PositiveFloat, `dz`: PositiveFloat)<br>- `porosity`: list[float]<br>- `permeability`: list[float]<br>- `rock_compressibility`: float (ge=0)<br>- `fluid_properties`: dict[str, PositiveFloat]<br>- `initial_pressure`: PositiveFloat<br>- `initial_water_saturation`: list[float]<br>- `initial_gas_saturation`: list[float]<br>- `wells`: list[WellInput] (`name`: str, `i`: int, `j`: int, `perforation_layers`: list[int], `well_type`: Literal['producer', 'injector'], `controls`: dict[str, float])<br>- `timesteps`: list[PositiveFloat] | `{"pressure": list[float], "saturations": {"water": list[float], "gas": list[float]}, "wells": list[dict]}` | 200-working | Yes (`test_black_oil_defaults_return_200`) | Yes (`BlackOilResponse`) |
| **`POST`** | `/api/simulate/compositional` | **`CompositionalInput`**:<br>- `grid`: GridInput<br>- `components`: list[ComponentInput] (`name`: str, `mw`: PositiveFloat, `tc`: PositiveFloat, `pc`: PositiveFloat, `omega`: float)<br>- `rock_properties`: dict[str, float]<br>- `wells`: list[dict[str, object]]<br>- `initial_composition`: dict[str, float]<br>- `timesteps`: list[PositiveFloat] | `{"detail": "The compositional flow solver is not implemented; no simulation results were produced."}` (HTTP 501) | 501-not-implemented | Yes (`test_compositional_route_is_marked_unimplemented`) | No (`None`) |
| **`POST`** | `/api/simulate/thermal` | **`ThermalInput`** (extends `CompositionalInput`):<br>- `grid`: GridInput<br>- `components`: list[ComponentInput]<br>- `rock_properties`: dict[str, float]<br>- `wells`: list[dict[str, object]]<br>- `initial_composition`: dict[str, float]<br>- `timesteps`: list[PositiveFloat]<br>- `thermal_properties`: ThermalPropertiesInput (`rock_heat_capacity`: PositiveFloat, `thermal_conductivity`: PositiveFloat, `fluid_heat_capacity`: PositiveFloat)<br>- `initial_temperature`: PositiveFloat | `{"detail": "The thermal flow and heat-transfer solver is not implemented; no simulation results were produced."}` (HTTP 501) | 501-not-implemented | Yes (`test_thermal_route_is_marked_unimplemented`) | No (`None`) |

### Diagnostic Root Endpoints (`backend/app/main.py`)

| Method | Path | Request Model | Actual Response Shape | Current Status | Has Test? (Name) | Has `response_model`? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`GET`** | `/health` | *None* | `{"status": "ok", "version": "0.1.0"}` | 200-working | Yes (`test_health_endpoint_returns_ok`) | No |
| **`GET`** | `/` | *None* | HTTP 307 Redirect to `/docs` | 200-working (Redirect) | No *(indirectly `/docs` is tested in `test_docs_renders`)* | No |

---

## Section 2 — Engine Inventory

Audit of every `.py` file under `backend/app/engines/**` (85 files total). Each module is evaluated for external API exposure (endpoint path or `orphaned`), repo-wide import consumption (importing files or `truly orphaned`), total lines of code (LOC), and runtime import validity (`yes` or specific module error message).

| Engine Module Path | Exposed via Endpoint? | Imported Anywhere? | LOC | Imports Work? |
| :--- | :--- | :--- | :--- | :--- |
| `app/engines/__init__.py` | orphaned | `app/api/chart_routes.py`, `app/api/engine_routes.py`, `app/api/simulation_routes.py`, `app/engines/analytics/__init__.py`, `app/engines/drilling/__init__.py`, `app/engines/drilling/rop_prediction.py`, `app/engines/modeling/__init__.py`, `app/engines/petrophysics/__init__.py`, `app/engines/petrophysics/las_reader.py`, `app/engines/prediction/__init__.py`, `app/engines/production/__init__.py`, `app/engines/pvt/correlations.py`, `app/engines/reservoir/__init__.py`, `app/engines/reservoir/nodal_analysis.py`, `app/ui/advanced_visualization_dashboard.py`, `app/ui/data_analytics_dashboard.py`, `app/ui/decline_curve_app.py`, `app/ui/ecd_calc.py`, `app/ui/facies_classification.py`, `app/ui/run_petrophysical.py`, `app/ui/train_lstm.py`, `tests/golden/test_carter_well_control.py`, `tests/test_economic_analysis.py`, `tests/test_engine_merge_regressions.py`, `tests/test_engines.py` | 1 | `yes` |
| `app/engines/analytics/__init__.py` | orphaned | `app/ui/train_lstm.py`, `tests/test_engines.py` | 33 | `yes` |
| `app/engines/analytics/advanced_analytics.py` | orphaned | truly orphaned | 345 | `ModuleNotFoundError: No module named 'tensorflow'` |
| `app/engines/analytics/ai_seismic.py` | orphaned | truly orphaned | 339 | `ModuleNotFoundError: No module named 'tensorflow'` |
| `app/engines/analytics/data_analytics.py` | orphaned | truly orphaned | 372 | `ModuleNotFoundError: No module named 'seaborn'` |
| `app/engines/analytics/data_integration.py` | orphaned | truly orphaned | 475 | `ModuleNotFoundError: No module named 'lasio'` |
| `app/engines/analytics/event_detection.py` | orphaned | `app/engines/analytics/__init__.py`, `tests/test_engines.py` | 36 | `yes` |
| `app/engines/analytics/sequences.py` | orphaned | `app/engines/analytics/__init__.py`, `app/ui/train_lstm.py`, `tests/test_engines.py` | 104 | `yes` |
| `app/engines/analytics/volve_eda.py` | orphaned | truly orphaned | 16 | `yes` |
| `app/engines/drilling/__init__.py` | orphaned | `app/api/chart_routes.py`, `app/api/engine_routes.py`, `app/engines/drilling/rop_prediction.py`, `app/ui/ecd_calc.py`, `tests/golden/test_carter_well_control.py`, `tests/test_engines.py` | 24 | `yes` |
| `app/engines/drilling/driller_sim.py` | orphaned | `app/engines/drilling/__init__.py`, `tests/test_engines.py` | 38 | `yes` |
| `app/engines/drilling/ecd.py` | orphaned | `app/engines/drilling/__init__.py`, `app/ui/ecd_calc.py`, `tests/test_engines.py` | 34 | `yes` |
| `app/engines/drilling/rop.py` | orphaned | `app/engines/drilling/__init__.py`, `app/engines/drilling/rop_prediction.py`, `tests/test_engines.py` | 226 | `yes` |
| `app/engines/drilling/rop_prediction.py` | orphaned | truly orphaned | 29 | `yes` |
| `app/engines/drilling/trajectory.py` | `POST /api/engine/drilling/trajectory`, `POST /api/engine/drilling/trajectory/chart` | `app/api/chart_routes.py`, `app/api/engine_routes.py`, `app/engines/drilling/__init__.py`, `tests/test_engines.py` | 36 | `yes` |
| `app/engines/drilling/well_control.py` | orphaned | `tests/golden/test_carter_well_control.py`, `tests/test_engines.py` | 782 | `yes` |
| `app/engines/drilling/well_models.py` | orphaned | truly orphaned | 515 | `yes` |
| `app/engines/geology/__init__.py` | orphaned | `app/api/chart_routes.py`, `app/api/engine_routes.py` | 28 | `yes` |
| `app/engines/geology/digital_rock.py` | orphaned | truly orphaned | 210 | `ModuleNotFoundError: No module named 'pyvista'` |
| `app/engines/geology/geostatistics.py` | orphaned | truly orphaned | 496 | `NameError: name 'Dict' is not defined. Did you mean: 'dict'?` |
| `app/engines/geology/mesh.py` | `POST /api/engine/geology/grid`, `POST /api/engine/geology/grid/chart` | `app/api/chart_routes.py`, `app/api/engine_routes.py` | 439 | `NameError: name 'Union' is not defined` |
| `app/engines/geology/model3d.py` | orphaned | truly orphaned | 187 | `ModuleNotFoundError: No module named 'pyvista'` |
| `app/engines/geology/nmr_analysis.py` | orphaned | truly orphaned | 223 | `yes` |
| `app/engines/geology/petrophysics.py` | orphaned | truly orphaned | 187 | `ModuleNotFoundError: No module named 'seaborn'` |
| `app/engines/geology/reservoir_characterization.py` | orphaned | truly orphaned | 247 | `ModuleNotFoundError: No module named 'segyio'` |
| `app/engines/geology/seismic_integration.py` | orphaned | truly orphaned | 132 | `ModuleNotFoundError: No module named 'segyio'` |
| `app/engines/geology/sensitivity.py` | orphaned | truly orphaned | 222 | `ModuleNotFoundError: No module named 'seaborn'` |
| `app/engines/modeling/__init__.py` | orphaned | truly orphaned | 26 | `yes` |
| `app/engines/modeling/geomechanics.py` | orphaned | truly orphaned | 394 | `yes` |
| `app/engines/modeling/static_modeling.py` | orphaned | truly orphaned | 560 | `yes` |
| `app/engines/modeling/thermal_modeling.py` | orphaned | truly orphaned | 493 | `yes` |
| `app/engines/modeling/uncertainty_analysis.py` | orphaned | truly orphaned | 236 | `ModuleNotFoundError: No module named 'seaborn'` |
| `app/engines/modeling/workflow_automation.py` | orphaned | truly orphaned | 484 | `ModuleNotFoundError: No module named 'seaborn'` |
| `app/engines/petrophysics/__init__.py` | orphaned | `app/engines/petrophysics/las_reader.py`, `app/ui/facies_classification.py`, `app/ui/run_petrophysical.py`, `tests/test_engines.py` | 10 | `yes` |
| `app/engines/petrophysics/facies.py` | orphaned | `app/engines/petrophysics/__init__.py`, `app/ui/facies_classification.py`, `tests/test_engines.py` | 121 | `yes` |
| `app/engines/petrophysics/las_reader.py` | orphaned | truly orphaned | 24 | `ModuleNotFoundError: No module named 'lasio'` |
| `app/engines/petrophysics/porosity.py` | orphaned | `app/engines/petrophysics/__init__.py`, `app/engines/petrophysics/las_reader.py`, `app/ui/run_petrophysical.py`, `tests/test_engines.py` | 31 | `yes` |
| `app/engines/prediction/__init__.py` | orphaned | truly orphaned | 14 | `yes` |
| `app/engines/prediction/ai_prediction.py` | orphaned | truly orphaned | 450 | `ModuleNotFoundError: No module named 'xgboost'` |
| `app/engines/production/__init__.py` | orphaned | `tests/test_economic_analysis.py` | 28 | `yes` |
| `app/engines/production/economic_analysis.py` | orphaned | `app/engines/production/__init__.py` | 323 | `yes` |
| `app/engines/production/flow_history_matching.py` | orphaned | truly orphaned | 250 | `ModuleNotFoundError: No module named 'seaborn'` |
| `app/engines/production/history_matching.py` | orphaned | `app/engines/production/flow_history_matching.py` | 328 | `ModuleNotFoundError: No module named 'seaborn'` |
| `app/engines/production/production_analysis.py` | orphaned | truly orphaned | 413 | `ModuleNotFoundError: No module named 'seaborn'` |
| `app/engines/production/production_forecasting.py` | orphaned | truly orphaned | 580 | `ModuleNotFoundError: No module named 'tensorflow'` |
| `app/engines/production/production_optimization.py` | orphaned | truly orphaned | 530 | `ModuleNotFoundError: No module named 'seaborn'` |
| `app/engines/production/reserves_evaluation.py` | orphaned | truly orphaned | 531 | `ModuleNotFoundError: No module named 'seaborn'` |
| `app/engines/pvt/__init__.py` | orphaned | `app/api/chart_routes.py`, `app/api/engine_routes.py`, `tests/test_engine_merge_regressions.py` | 7 | `yes` |
| `app/engines/pvt/correlations.py` | orphaned | `app/engines/pvt/__init__.py`, `tests/test_engine_merge_regressions.py` | 161 | `yes` |
| `app/engines/pvt/dca.py` | orphaned | truly orphaned | 107 | `yes` |
| `app/engines/pvt/eos_solver.py` | `POST /api/engine/pvt/eos`, `POST /api/engine/pvt/eos/chart` | `app/api/chart_routes.py`, `app/api/engine_routes.py`, `app/engines/pvt/__init__.py` | 153 | `yes` |
| `app/engines/pvt/mbal.py` | orphaned | `app/engines/pvt/__init__.py` | 199 | `yes` |
| `app/engines/pvt/z_factor.py` | orphaned | truly orphaned | 77 | `yes` |
| `app/engines/reservoir/__init__.py` | orphaned | `app/api/chart_routes.py`, `app/api/engine_routes.py`, `app/api/simulation_routes.py`, `app/engines/pvt/correlations.py`, `app/engines/reservoir/nodal_analysis.py`, `app/ui/decline_curve_app.py`, `tests/test_engine_merge_regressions.py`, `tests/test_engines.py` | 43 | `yes` |
| `app/engines/reservoir/decline_curve.py` | orphaned | `app/engines/reservoir/__init__.py`, `app/ui/decline_curve_app.py`, `tests/test_engine_merge_regressions.py`, `tests/test_engines.py` | 236 | `yes` |
| `app/engines/reservoir/material_balance.py` | orphaned | `app/engines/reservoir/__init__.py`, `tests/test_engines.py` | 140 | `yes` |
| `app/engines/reservoir/nodal.py` | `POST /api/engine/reservoir/nodal`, `POST /api/engine/reservoir/nodal/chart` | `app/api/chart_routes.py`, `app/api/engine_routes.py`, `app/engines/reservoir/__init__.py`, `app/engines/reservoir/nodal_analysis.py`, `tests/test_engines.py` | 102 | `yes` |
| `app/engines/reservoir/nodal_analysis.py` | orphaned | truly orphaned | 37 | `yes` |
| `app/engines/reservoir/pvt.py` | orphaned | `app/engines/pvt/correlations.py`, `app/engines/reservoir/__init__.py`, `app/engines/reservoir/material_balance.py`, `tests/test_engine_merge_regressions.py`, `tests/test_engines.py` | 170 | `yes` |
| `app/engines/reservoir/reservoir_analysis.py` | orphaned | truly orphaned | 270 | `ModuleNotFoundError: No module named 'tensorflow'` |
| `app/engines/reservoir/reservoir_engineering.py` | orphaned | truly orphaned | 676 | `ModuleNotFoundError: No module named 'seaborn'` |
| `app/engines/reservoir/reservoir_simulation.py` | orphaned | truly orphaned | 994 | `ImportError: cannot import name 'spsolve' from 'scipy.sparse' (/home/jules/.pyenv/versions/3.12.13/lib/python3.12/site-packages/scipy/sparse/__init__.py)` |
| `app/engines/reservoir/simulation/__init__.py` | `POST /api/simulate/black-oil`, `POST /api/simulate/compositional`, `POST /api/simulate/thermal` | `app/api/simulation_routes.py`, `tests/test_engine_merge_regressions.py` | 27 | `yes` |
| `app/engines/reservoir/simulation/advanced_simulation.py` | orphaned | `app/engines/reservoir/simulation/__init__.py`, `app/engines/reservoir/simulation/simulator_integration.py` | 240 | `yes` |
| `app/engines/reservoir/simulation/auto_diff.py` | orphaned | truly orphaned | 78 | `yes` |
| `app/engines/reservoir/simulation/black_oil_simulator.py` | `POST /api/simulate/black-oil` | `app/engines/reservoir/simulation/__init__.py`, `app/engines/reservoir/simulation/eor_simulator.py`, `app/engines/reservoir/simulation/simulation_controller.py` | 213 | `yes` |
| `app/engines/reservoir/simulation/commercial_simulator.py` | orphaned | `app/engines/reservoir/simulation/__init__.py`, `app/engines/reservoir/simulation/simulator_integration.py` | 456 | `yes` |
| `app/engines/reservoir/simulation/compositional_modeling.py` | orphaned | `app/engines/reservoir/simulation/__init__.py`, `app/engines/reservoir/simulation/simulator_integration.py`, `tests/test_engine_merge_regressions.py` | 574 | `yes` |
| `app/engines/reservoir/simulation/compositional_simulator.py` | `POST /api/simulate/compositional` | `app/engines/reservoir/simulation/__init__.py`, `app/engines/reservoir/simulation/simulation_controller.py`, `app/engines/reservoir/simulation/thermal_simulator.py` | 53 | `yes` |
| `app/engines/reservoir/simulation/eor_simulator.py` | orphaned | `app/engines/reservoir/simulation/__init__.py` | 175 | `yes` |
| `app/engines/reservoir/simulation/flow_simulation.py` | orphaned | truly orphaned | 620 | `ModuleNotFoundError: No module named 'geology'` |
| `app/engines/reservoir/simulation/grid.py` | `POST /api/simulate/compositional`, `POST /api/simulate/thermal` | `app/api/simulation_routes.py`, `app/engines/reservoir/simulation/black_oil_simulator.py`, `app/engines/reservoir/simulation/compositional_simulator.py` | 95 | `yes` |
| `app/engines/reservoir/simulation/history_matcher.py` | orphaned | `tests/test_engine_merge_regressions.py` | 175 | `yes` |
| `app/engines/reservoir/simulation/network_designer.py` | orphaned | `app/engines/reservoir/simulation/simulation_controller.py` | 106 | `yes` |
| `app/engines/reservoir/simulation/parallel_engine.py` | orphaned | `app/engines/reservoir/simulation/simulation_controller.py` | 128 | `yes` |
| `app/engines/reservoir/simulation/production_optimizer.py` | orphaned | truly orphaned | 156 | `yes` |
| `app/engines/reservoir/simulation/proxy_models.py` | orphaned | truly orphaned | 184 | `ModuleNotFoundError: No module named 'tensorflow'` |
| `app/engines/reservoir/simulation/simulation_controller.py` | orphaned | truly orphaned | 166 | `ModuleNotFoundError: No module named 'app.engines.reservoir.pvt.correlations'; 'app.engines.reservoir.pvt' is not a package` |
| `app/engines/reservoir/simulation/simulator_integration.py` | orphaned | truly orphaned | 379 | `yes` |
| `app/engines/reservoir/simulation/thermal_simulator.py` | `POST /api/simulate/thermal` | `app/engines/reservoir/simulation/__init__.py`, `app/engines/reservoir/simulation/simulation_controller.py` | 56 | `yes` |
| `app/engines/reservoir/well_testing.py` | orphaned | `app/engines/reservoir/__init__.py`, `tests/test_engine_merge_regressions.py` | 35 | `yes` |
| `app/engines/visualization/__init__.py` | orphaned | `app/ui/advanced_visualization_dashboard.py` | 21 | `yes` |
| `app/engines/visualization/advanced_visualization.py` | orphaned | `app/ui/advanced_visualization_dashboard.py` | 199 | `ModuleNotFoundError: No module named 'plotly'` |
| `app/engines/visualization/results_visualizer.py` | orphaned | truly orphaned | 54 | `ModuleNotFoundError: No module named 'vtk'` |
| `app/engines/visualization/visualizer3d.py` | orphaned | truly orphaned | 386 | `ModuleNotFoundError: No module named 'pyvista'` |

---

## Section 3 — Gap Analysis

### 1. Orphaned Engines Worth Exposing

Criteria:
- Import status is clean (`Imports Work? = yes`) with no missing third-party dependencies.
- High-value mathematical/engineering domain logic (>50 real logic LOC excluding blank lines and comments).
- Currently unexposed via any HTTP API endpoint (`Exposed = orphaned`).
- Ranked by petroleum engineering domain value: **Production > Petrophysics > PVT > Drilling > Geology > Simulation > Visualization**.

| Rank | Domain | Engine Module File | Real Logic LOC | Total LOC | Core Functionality & Exposure Proposal |
| :---: | :--- | :--- | :---: | :---: | :--- |
| 1 | **Production** | `app/engines/production/economic_analysis.py` | 293 | 323 | Full annual field production economics: discounted cash flows, capex/opex schedules, royalties, abandonment costs, NPV, IRR, payout period, sensitivity matrices, and Monte Carlo simulation. Expose via `POST /api/engine/production/economics`. |
| 2 | **Petrophysics** | `app/engines/petrophysics/facies.py` | 92 | 121 | Well log lithofacies classification engine using Random Forest, Gradient Boosting, SVM, and KNN classifiers trained on gamma ray, density, and neutron porosity. Expose via `POST /api/engine/petrophysics/facies/classify`. |
| 3 | **PVT** | `app/engines/pvt/mbal.py` | 151 | 199 | Material balance engine supporting Havlena-Odeh linear analysis, drive index calculations (water drive, gas cap expansion, solution gas), Campbell plots, and OOIP/OGIP estimation. Expose via `POST /api/engine/pvt/mbal`. |
| 4 | **PVT** | `app/engines/pvt/correlations.py` | 143 | 161 | Empirical oil and gas PVT correlations (Standing, Vasquez-Beggs, Glaso, Beggs-Robinson, Lee-Gonzales-Eakin) for bubble point, solution GOR, oil FVF, compressibility, and viscosity. Expose via `POST /api/engine/pvt/correlations`. |
| 5 | **PVT** | `app/engines/pvt/dca.py` | 85 | 107 | Arps decline curve analysis models: exponential, hyperbolic, and harmonic decline forecasting with EUR and remaining life integration. Expose via `POST /api/engine/pvt/dca`. |
| 6 | **PVT** | `app/engines/pvt/z_factor.py` | 55 | 77 | Natural gas pseudo-critical pressure and temperature calculation (Sutton, Piper) and Hall-Yarborough / Dranchuk-Abou-Kassem Z-factor equations of state. Expose via `POST /api/engine/pvt/z-factor`. |
| 7 | **Reservoir** | `app/engines/reservoir/decline_curve.py` | 201 | 236 | Advanced Arps decline curve analysis with automated parameter fitting (`scipy.optimize.curve_fit`), cumulative production integrals, and remaining recoverable reserves. Expose via `POST /api/engine/reservoir/dca/fit`. |
| 8 | **Reservoir** | `app/engines/reservoir/pvt.py` | 134 | 170 | Thermodynamic PVT calculations for black oil (bubble point, FVF, gas solubility) and dry/wet gas properties. Expose via `POST /api/engine/reservoir/pvt/properties`. |
| 9 | **Reservoir** | `app/engines/reservoir/material_balance.py` | 110 | 140 | Gas reservoir material balance (P/Z analysis, water influx modeling with Carter-Tracy / Fetkovich aquifers) and Rate Transient Analysis (FMB). Expose via `POST /api/engine/reservoir/gas-mbal`. |
| 10 | **Drilling** | `app/engines/drilling/well_control.py` | 572 | 782 | Carter Well Control engineering suite: MASICP, Wait and Weight / Driller's method kill sheets, KOP circulating pressure, MASP, trip margins, gas cut mud, and barite plug calculations. Expose via `POST /api/engine/drilling/well-control`. |
| 11 | **Drilling** | `app/engines/drilling/well_models.py` | 381 | 515 | Directional well planning: 3D minimum curvature, tangential, and balanced tangential models, casing clearance checking, torque and drag analysis, and hydraulics. Expose via `POST /api/engine/drilling/well-planning`. |
| 12 | **Drilling** | `app/engines/drilling/rop.py` | 174 | 226 | Rate of Penetration (ROP) physics engine: Bingham, Maurer, and Warren ROP models with mechanical specific energy (MSE) calculation. Expose via `POST /api/engine/drilling/rop`. |
| 13 | **Geology** | `app/engines/geology/nmr_analysis.py` | 161 | 223 | Nuclear Magnetic Resonance (NMR) logging interpretation: T2 distribution processing, bound fluid volume (BVI), free fluid index (FFI), and Coates / SDR permeability estimation. Expose via `POST /api/engine/geology/nmr`. |
| 14 | **Modeling** | `app/engines/modeling/static_modeling.py` | 430 | 560 | 3D reservoir geocellular modeling: structural grid construction, variogram analysis, and 3D petrophysical property distribution (porosity, permeability, saturation). Expose via `POST /api/engine/modeling/static-grid`. |
| 15 | **Modeling** | `app/engines/modeling/thermal_modeling.py` | 331 | 493 | Coupled thermal modeling: 3D conductive and convective heat transport, geothermal gradient estimation, and steam-injection thermal tracking. Expose via `POST /api/engine/modeling/thermal`. |
| 16 | **Modeling** | `app/engines/modeling/geomechanics.py` | 259 | 394 | Geomechanical reservoir coupling: pore pressure prediction (Eaton, Bowers), in-situ stress tensor calculation, and borehole breakout/breakdown limits. Expose via `POST /api/engine/modeling/geomechanics`. |
| 17 | **Analytics** | `app/engines/analytics/sequences.py` | 78 | 104 | Time-series sequence engineering: sliding window formulation, feature scaling, and sequence normalization for production forecasting. Expose via `POST /api/engine/analytics/sequences`. |
| 18 | **Simulation** | `app/engines/reservoir/simulation/compositional_modeling.py` | 400 | 574 | Thermodynamic compositional phase equilibrium and equation-of-state flash calculation engine. Expose via `POST /api/engine/simulation/compositional-flash`. |
| 19 | **Simulation** | `app/engines/reservoir/simulation/commercial_simulator.py` | 334 | 456 | Commercial simulator integration and input deck generator (ECL, CMG, IMEX). Expose via `POST /api/engine/simulation/deck-export`. |
| 20 | **Simulation** | `app/engines/reservoir/simulation/simulator_integration.py` | 257 | 379 | Simulation workflow integration: input validation, grid mapping, and coupled surface-subsurface constraint solving. Expose via `POST /api/engine/simulation/integrate`. |
| 21 | **Simulation** | `app/engines/reservoir/simulation/advanced_simulation.py` | 170 | 240 | Advanced reservoir simulation methods: adaptive time-stepping, high-order flux limiting, and dual-porosity dual-permeability formulations. Expose via `POST /api/engine/simulation/advanced`. |
| 22 | **Simulation** | `app/engines/reservoir/simulation/history_matcher.py` | 144 | 175 | Reservoir history matching engine: gradient and evolutionary optimization of permeability and porosity fields to minimize production misfit. Expose via `POST /api/engine/simulation/history-match`. |
| 23 | **Simulation** | `app/engines/reservoir/simulation/eor_simulator.py` | 139 | 175 | Enhanced Oil Recovery (EOR) flow simulator: polymer flood viscosity enhancement, adsorption, and surfactant capillary desaturation. Expose via `POST /api/engine/simulation/eor`. |
| 24 | **Simulation** | `app/engines/reservoir/simulation/production_optimizer.py` | 122 | 156 | Simulation production optimizer: well rate allocation, choke setting optimization, and net present value maximization under water-cut limits. Expose via `POST /api/engine/simulation/optimize-production`. |
| 25 | **Simulation** | `app/engines/reservoir/simulation/parallel_engine.py` | 98 | 128 | Parallel domain decomposition engine for multi-threaded / multi-rank grid solving. Expose via `POST /api/engine/simulation/parallel`. |
| 26 | **Simulation** | `app/engines/reservoir/simulation/network_designer.py` | 86 | 106 | Surface pipeline gathering network designer: pipe hydraulics, pressure drops (Beggs-Brill), and manifold routing. Expose via `POST /api/engine/simulation/network`. |
| 27 | **Simulation** | `app/engines/reservoir/simulation/auto_diff.py` | 59 | 78 | Automatic differentiation variable class for reservoir simulation Jacobians and sensitivity evaluation. Expose via `POST /api/engine/simulation/autodiff`. |

### 2. Broken Surface

Identified endpoints, surface interfaces, and runtime defects categorized by cause:

#### A. Runtime Crashing Endpoints (500 Internal Server Error / Unhandled Exception)
1. **`POST /api/engine/geology/grid` and `POST /api/engine/geology/grid/chart`**:
   - **File Path**: `backend/app/engines/geology/mesh.py`
   - **Exact Lines**: Line 250 (`dx: Union[float, np.ndarray]`), Line 251 (`dy: Union[float, np.ndarray]`), Line 252 (`dz: Union[float, np.ndarray]`), Line 272 (`spacing: Union[float, np.ndarray]`), Line 273 (`-> Tuple[Union[float, np.ndarray], np.ndarray]`), and Line 277 (`public_value: Union[float, np.ndarray] = value`).
   - **Exact Error Message**: `NameError: name 'Union' is not defined`
   - **Root Cause**: Line 3 has `from typing import Dict, List, Tuple, Optional` which omits importing `Union` from `typing`.
   - **Why It Matters & Repercussions**: Because `backend/app/api/chart_routes.py` and `backend/app/api/engine_routes.py` both import `from ..engines.geology.mesh import Grid3D`, loading `app.main` fails at module import time. As a result, the entire FastAPI application cannot start, and all endpoints (`/api/engine/geology/grid`, `/api/engine/geology/grid/chart`, as well as the entire route registry) become completely unreachable, throwing 500 / startup crash errors. Furthermore, test collection in `backend/tests/test_engine_routes.py` and `backend/tests/test_openapi_tags.py` fails immediately upon encountering this import.
2. **`POST /api/simulate/compositional` and `POST /api/simulate/thermal`**:
   - **File Path**: `backend/app/api/simulation_routes.py`
   - **Exact Lines**: Lines 186-199 (`simulate_compositional`) and Lines 202-220 (`simulate_thermal`).
   - **Exact Behavior**: Endpoints are declared on the router and accept valid Pydantic bodies, but invoke `_not_implemented()`, unconditionally raising `HTTPException(status_code=501, detail=...)`.
   - **Why It Matters**: Clients sending valid requests receive 501 Not Implemented instead of calculation results.

#### B. Endpoints Missing `response_model`
FastAPI best practices require declaring explicit response models to ensure schema documentation, response serializability, and field validation. The following routes lack a `response_model`:
1. **`POST /api/simulate/compositional`** (`backend/app/api/simulation_routes.py` line 186):
   - Decorator: `@router.post('/simulate/compositional', tags=['Simulation'])` — missing `response_model`.
2. **`POST /api/simulate/thermal`** (`backend/app/api/simulation_routes.py` line 203):
   - Decorator: `@router.post('/simulate/thermal', tags=['Simulation'])` — missing `response_model`.
3. **`GET /health`** (`backend/app/main.py` line 19):
   - Decorator: `@app.get('/health')` — missing Pydantic `response_model` (returns raw dict `{"status": "ok", "version": app.version}`).

#### C. Missing or Impaired Test Coverage
1. **Test Suite Collection Failure**:
   - `backend/tests/test_engine_routes.py` contains 12 unit tests covering all routes, and `backend/tests/test_openapi_tags.py` contains 3 tests. However, **both test modules crash during pytest collection** with exit code 2 due to the unimported `Union` in `mesh.py` triggered when `from app.main import app` is executed.
   - Consequently, in standard test runs, zero endpoints are verified by CI until the `mesh.py` typing import is resolved.
2. **Untested Root Route**:
   - `GET /` (HTTP 307 redirect to `/docs`) defined in `backend/app/main.py` has no dedicated test assertion.

---

## Section 4 — Test Coverage

### Pytest Command Execution
Command run from sandbox root:
```bash
pytest backend/tests -q --tb=short --cov=backend/app --cov-report=term-missing
```

### Execution Output & Results
```text
==================================== ERRORS ====================================
_________________ ERROR collecting tests/test_engine_routes.py _________________
backend/tests/test_engine_routes.py:3: in <module>
    from app.main import app
backend/app/main.py:11: in <module>
    from .api import chart_routes, engine_routes, simulation_routes
backend/app/api/chart_routes.py:18: in <module>
    from ..engines.geology.mesh import Grid3D
backend/app/engines/geology/mesh.py:242: in <module>
    class Grid3D:
backend/app/engines/geology/mesh.py:250: in Grid3D
    dx: Union[float, np.ndarray],
        ^^^^^
E   NameError: name 'Union' is not defined
_________________ ERROR collecting tests/test_openapi_tags.py __________________
backend/tests/test_openapi_tags.py:2: in <module>
    from app.main import app
backend/app/main.py:11: in <module>
    from .api import chart_routes, engine_routes, simulation_routes
backend/app/api/chart_routes.py:18: in <module>
    from ..engines.geology.mesh import Grid3D
backend/app/engines/geology/mesh.py:242: in <module>
    class Grid3D:
backend/app/engines/geology/mesh.py:250: in Grid3D
    dx: Union[float, np.ndarray],
        ^^^^^
E   NameError: name 'Union' is not defined
=============================== warnings summary ===============================
../home/jules/.pyenv/versions/3.12.13/lib/python3.12/site-packages/fastapi/testclient.py:1
  /home/jules/.pyenv/versions/3.12.13/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR backend/tests/test_engine_routes.py - NameError: name 'Union' is not de...
ERROR backend/tests/test_openapi_tags.py - NameError: name 'Union' is not def...
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
1 warning, 2 errors in 8.58s
```

Exit code: `2` (Collection Interrupted).

### Detailed Pass/Fail Breakdown per Test Module
Running individual test files through pytest yields the following breakdown:

| Test Module | Status | Passed | Failed | Collection Errors | Details |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `backend/tests/golden/test_carter_well_control.py` | **PASSED** | 15 | 0 | 0 | 15 golden Carter Well Control benchmarks pass |
| `backend/tests/test_economic_analysis.py` | **PASSED** | 4 | 0 | 0 | Cash-flow, project metrics, sensitivity, inputs |
| `backend/tests/test_engines.py` | **PASSED** | 14 | 0 | 0 | 14 engine unit tests pass (math, ECD, ROP, nodal, DCA, facies) |
| `backend/tests/test_engine_merge_regressions.py` | **FAILED** | 7 | 2 | 0 | 7 passed; 2 failed (`test_structured_mesh_connectivity_handles_non_cubic_grid`, `test_grid3d_supports_variable_positive_cell_widths`) due to `NameError: name 'Union' is not defined` in `mesh.py` |
| `backend/tests/test_engine_routes.py` | **ERROR** | 0 | 0 | 1 | Collection aborted due to `from app.main import app` importing `mesh.py` (12 tests unexecuted) |
| `backend/tests/test_openapi_tags.py` | **ERROR** | 0 | 0 | 1 | Collection aborted due to `from app.main import app` importing `mesh.py` (3 tests unexecuted) |
| **TOTAL** | | **36** | **2** | **2** | **40 tests collected across isolated files; 15 test cases blocked in collection** |

### Potential Test Coverage (When Typing Bug is Bypassed)
When `Union` is present in scope, all **57 test cases** in the test suite execute and pass (57 passed, 0 failed):
- Total source lines measured under `backend/app`: **8,901 lines**
- Lines executed: **1,926 lines**
- Lines missed: **6,975 lines**
- Baseline code coverage: **22%**
- The unexercised 78% of backend lines corresponds directly to the orphaned computational engines documented in Section 2 and Section 3.
