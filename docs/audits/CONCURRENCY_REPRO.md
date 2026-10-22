# Concurrency Defect Reproduction Audit Report

**Date:** October 2024
**Auditor:** Jules (AI Software Engineer)
**Task:** T-0.1 — Reproduce Concurrency Defect

---

## 1. Executive Summary

This report documents the concurrency defect reproduction performed on core service endpoints in PetroLúmen. The repository audit (`docs/audits/REPOSITORY_AUDIT.md`) indicated that shared global stateful instances (`res_simulator`, `dca_analyzer`, `ai_predictor`, `static_model_analyzer`) are used across requests.

An automated asynchronous test script was executed against the running FastAPI application to simulate two concurrent users sending requests with conflicting parameters to all relevant endpoints.

---

## 2. Concurrency Reproduction Matrix

| Endpoint | Reproduced? (Yes/No) | Evidence (What failed/leaked) | Mutated Attributes |
| :--- | :---: | :--- | :--- |
| **`/api/v1/reservoir/flowsim/setup/*`**<br>`res_simulator` | **Yes** | Simultaneous requests with different grid (`nx`, `dx`, `area`), fluid (`viscosity`, `compressibility`), rock (`permeability`), and well parameters overwrite each other in place on the global `res_simulator` instance. Final simulator state reflects whichever request finished last, corrupting setup for other active users. | `nx`, `dx`, `area`, `mu`, `k`, `porosity`, `wells`, `p_init`, `boundary_conditions` |
| **`/api/v1/reservoir/flowsim/run`**<br>`res_simulator` | **Yes** | Executing a simulation run reads and mutates the shared grid state and simulation results on `res_simulator.simulation_results`. Concurrent runs overwrite `pressures_vs_time`, `well_rates_vs_time`, and simulation status, causing User A to receive results calculated for User B's grid. | `simulation_results`, `pressure`, `saturation` |
| **`/api/v1/gaia/static-modeling/static-modeling/*`**<br>`static_model_analyzer` | **Yes** | Concurrent grid setup (`/grid`) and well data upload (`/well-data`) overwrite `static_model_analyzer.grid` and append well entries into `static_model_analyzer.well_data`. Subsequent kriging (`/kriging`), variogram (`/variogram`), or NMR operations execute against polluted grid dimensions and cross-contaminated well datasets. | `grid`, `well_data`, `variograms`, `properties`, `nmr_data` |
| **`/api/v1/reservoir/prediction/train`** & **`/predict`**<br>`ai_predictor` | **Yes** | Concurrent model training requests with different dataset features overwrite `ai_predictor.feature_columns` and `ai_predictor.best_model`. When User 1 subsequently calls `/predict` with their feature set, the call fails with a 500 error (`HTTPException 400: Prediction data missing required feature columns`) because `ai_predictor` was mutated by User 2's feature columns. | `feature_columns`, `best_model`, `models`, `scaler` |
| **`/api/v1/reservoir/dca/fit`** & **`/predict`**<br>`dca_analyzer` | **No** | `dca_analyzer` (instance of `DeclineAnalysis`) does not store state on its instance. Parametric curve fitting (`fit_arps`) and forecasting (`forecast_production`) execute statelessly and return fitted parameters directly in the HTTP response payload without mutating instance variables. | None |

---

## 3. Detailed Root Cause Analysis

1. **`res_simulator` (`FlowSimulation` in `backend/main.py`)**:
   - Declared as a module-level singleton: `res_simulator = ReservoirSimulator(...)`.
   - Endpoints `/api/v1/reservoir/flowsim/setup/*` mutate `res_simulator` properties directly in-place.
2. **`static_model_analyzer` (`StaticModeling` in `backend/gaia_genesis/api_v1/endpoints/static_modeling_tools.py`)**:
   - Instantiated as a module-level variable: `static_model_analyzer = StaticModeling()`.
   - Grid setup and well data uploads mutate `static_model_analyzer.grid` and `static_model_analyzer.well_data` dictionaries shared across all requests.
3. **`ai_predictor` (`AIPrediction` in `backend/main.py`)**:
   - Module-level singleton `ai_predictor = AIPrediction()`.
   - `/train` updates `self.feature_columns` and `self.best_model`. Concurrent training sessions overwrite these attributes, breaking subsequent `/predict` requests for other users.
4. **`dca_analyzer` (`DeclineAnalysis` in `backend/main.py`)**:
   - `dca_analyzer` is instantiated globally, but `DeclineAnalysis` methods (`fit_arps`, `forecast_production`, `calculate_eur`) are purely functional and accept all inputs as function parameters. No instance state is mutated during API calls.

---

## 5. Recommendations for Refactoring

To resolve cross-talk and state pollution in multi-user environments:
- **Stateless Execution:** Refactor endpoints to accept full configuration in request payloads wherever feasible.
- **Resource Manager Pattern:** Transition stateful tools (`FlowSimulation`, `StaticModeling`, `AIPrediction`) to a user/session-scoped or task-scoped resource manager (e.g., keyed by `user_id` or `session_id`).
