# PetroLúmen Product Roadmap

This document outlines the near-term, medium-term, and long-term technical evolution of the PetroLúmen petroleum engineering workbench.

---

## 1. Near-term (next 3 months)

Expose and integrate the top 10 orphaned computational engines identified in [docs/backend_capability_audit.md Section 3.1](backend_capability_audit.md#1-orphaned-engines-worth-exposing) via typed FastAPI endpoints:

1. **`app/engines/production/economic_analysis.py`** (Rank 1): Expose annual field discounted cash flows, royalties, opex/capex schedules, NPV, IRR, and fiscal sensitivities via `POST /api/engine/production/economics` *(exposed on main)*.
2. **`app/engines/petrophysics/facies.py`** (Rank 2): Expose Random Forest / multi-model lithofacies classification from wireline log curves via `POST /api/engine/petrophysics/facies/classify` *(exposed on main)*.
3. **`app/engines/pvt/mbal.py`** (Rank 3): Expose Havlena-Odeh material balance analysis, drive indices, and OOIP/OGIP estimation via `POST /api/engine/pvt/mbal` *(exposed on main)*.
4. **`app/engines/pvt/correlations.py`** (Rank 4): Expose empirical oil and gas PVT correlations (Standing, Vasquez-Beggs, Beggs-Robinson, Lee-Gonzalez-Eakin) via `POST /api/engine/pvt/correlations`.
5. **`app/engines/pvt/dca.py`** (Rank 5): Expose Arps decline curve analysis models (exponential, hyperbolic, harmonic) and EUR calculations via `POST /api/engine/pvt/dca`.
6. **`app/engines/pvt/z_factor.py`** (Rank 6): Expose natural gas pseudo-critical properties and Hall-Yarborough / Dranchuk-Abou-Kassem Z-factor equations of state via `POST /api/engine/pvt/z-factor`.
7. **`app/engines/reservoir/decline_curve.py`** (Rank 7): Expose automated decline curve parameter fitting (`scipy.optimize.curve_fit`) and remaining recoverable reserve estimation via `POST /api/engine/reservoir/dca/fit`.
8. **`app/engines/reservoir/pvt.py`** (Rank 8): Expose thermodynamic black-oil and gas PVT property evaluations via `POST /api/engine/reservoir/pvt/properties`.
9. **`app/engines/reservoir/material_balance.py`** (Rank 9): Expose gas reservoir material balance ($P/Z$ analysis and aquifer influx modeling) via `POST /api/engine/reservoir/gas-mbal`.
10. **`app/engines/drilling/well_control.py`** (Rank 10): Expose Carter well control calculations (MASICP, Wait and Weight / Driller's method kill sheets, KOP circulating pressure, and barite plugs) via `POST /api/engine/drilling/well-control`.

---

## 2. Medium-term (3–12 months)

- **Real OPM Flow integration:** Assemble standardized `.DATA` simulation decks, trigger the external OPM Flow binary in a sandboxed subprocess runner, and parse output restart and summary vector files.
- **RESQML via resqpy:** Enable reading and writing of standardized RESQML EPC/HDF5 geological model formats for interoperability with commercial subsurface platforms.
- **Job queue (Celery/RQ):** Implement asynchronous background job dispatch with Redis to manage long-running numerical simulations, grid operations, and batch parameter sensitivity sweeps.
- **PostgreSQL persistence:** Introduce relational database persistence using SQLAlchemy and Alembic schema migrations to transition from stateless execution to persistent project and run management.
- **Ensemble uncertainty:** Provide Monte Carlo simulation runs, latin hypercube sampling, and tornado sensitivity analysis for probabilistic reserve estimations and risk assessment.

---

## 3. Long-term (12+ months)

For the detailed north-star architecture, technical philosophy, and multi-tier system vision, see [docs/ARCHITECTURE_VISION.md](ARCHITECTURE_VISION.md).

PetroLúmen envisions a fully open, modular petroleum engineering operating system that democratizes upstream computation without proprietary lock-in. Over the multi-year horizon, PetroLúmen will unite physics-based reservoir simulation (OPM Flow, JutulDarcy) with real-time drilling hydraulics, deep surface facility network solving, and AI-accelerated proxy models. The platform will deliver interactive 3D web and desktop spatial inspection, multi-user collaboration, automated history matching, and continuous field optimization workflows accessible to every engineer.

---

## 4. Known limitations

- `/api/simulate/compositional` → Returns HTTP 501 Not Implemented (compositional flow solver stubbed).
- `/api/simulate/thermal` → Returns HTTP 501 Not Implemented (thermal flow and heat-transfer solver stubbed).
- `black_oil_simulator.py` is a toy model; see its docstring for the limitations (physics is documented, not verified). Specifically, pressure is solved via an ad-hoc linear surrogate without true compressibility coupling, saturations are uncoupled without Darcy flux divergence or capillary pressure, and well conditions (`_apply_well_conditions`) are not implemented.
- No persistence layer (every run is stateless; results are held in memory during the request lifecycle only).
- No authentication or authorization layer (open local workbench access).
