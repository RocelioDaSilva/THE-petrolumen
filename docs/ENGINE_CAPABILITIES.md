# Backend Engineering Capabilities

This document describes the backend calculations reachable through the mounted
FastAPI application, followed by code that exists in `backend/app/engines/` but
is not exposed as a supported HTTP workflow. Route names and request/response
models are in [API_REFERENCE.md](API_REFERENCE.md).

**Engineering-use notice:** a calculation being implemented or covered by a
test is not a claim of field validation, regulatory acceptance, or suitability
for design-critical decisions. Verify inputs, units, correlation range, and
results independently with a qualified engineer.

## API-exposed calculations

| Capability | Method / implementation | Limitations and interpretation |
|---|---|---|
| **Mixture EOS Z-factor** | Peng–Robinson (PR) and Soave–Redlich–Kwong (SRK) cubic EOS in `engines/pvt/eos_solver.py`. The API returns the largest real cubic root (vapor-root Z); binary interaction coefficients default to zero. | The endpoint does not calculate liquid-root properties, volume translation, or phase stability. Its units are Pa and K and must be consistent with critical properties. EOS Z-factor is not a substitute for calibrated fluid characterization. |
| **Isothermal flash** | Wilson K-values with a bisection solution of the Rachford–Rice equation in `EosSolver.flash_calculation`. Users may supply initial K-values. | K-values remain fixed during the split. This is a screening flash, not fugacity-coefficient iteration or a converged thermodynamic-equilibrium flash. |
| **Black-oil and formation-water PVT** | `engines/reservoir/black_oil_pvt.py`: Standing/Beggs solution GOR and oil FVF, Beggs-Robinson/Vasquez-Beggs/Egbogah oil-viscosity options, Villena-Lanzi/Vasquez-Beggs oil compressibility, Lee-Gonzalez-Eakin gas viscosity, and McCain/Osif water properties. | Responses report correlation validity where implemented; out-of-range values are not field-calibrated. Water PVT intentionally does not apply an unverified below-bubble-point compressibility correction. Inputs and outputs are field-unit quantities as documented by each route. |
| **Chapter 2 PVT correlations** | `engines/reservoir/ppes_bridge.py` exposes Standing Rs/Bo, dead/saturated/undersaturated oil viscosity, low-pressure gas viscosity, oil/gas density, Bg/Eg, oil compressibility, Wichert-Aziz sour-gas correction, and Brill-Beggs Z-factor. | These are individual empirical correlations, not a fully coupled PVT table or compositional fluid characterization. Correlation-specific input ranges and units apply. |
| **Gas and rock compressibility** | `engines/reservoir/compressibility.py`: Newman's rock correlation for sandstone/limestone; Hall-Yarborough gas Z using Sutton pseudocritical properties; finite-difference derivative; phase-weighted total compressibility. | Newman's correlation is limited to consolidated sandstone/limestone and reports its porosity range; strict mode can reject out-of-range inputs. Gas derivative depends on the selected pressure step and Z-correlation convergence. Oil and water compressibility are supplied by the caller; total compressibility assumes saturations sum to one. |
| **Vogel IPR and nodal rate** | `engines/reservoir/nodal.py` and the ppes bridge implement Vogel IPR, inverse IPR curves, and an IPR/TPR intersection. TPR is represented by user-provided surface pressure and quadratic coefficients. | This is a simplified inflow/outflow model, not a multiphase tubing hydraulics or full nodal-analysis package. Results depend on the chosen coefficients and the assumptions of the Vogel relation. |
| **Exponential decline** | Chapter 8 ppes bridge functions calculate exponential decline rate and cumulative production. | Only exponential decline is exposed by this route. The decline constant and time must use consistent units; no economic limit, uncertainty model, or automatic decline-regime selection is applied. |
| **Material balance** | `engines/pvt/mbal.py` is called by `/api/engine/pvt/mbal` for oil or gas Havlena–Odeh scalar estimates. | If PVT data is omitted, the route inserts two default PVT points. The engine returns a scalar; drive indices are not calculated and the API returns `drive_indices: null`. This is not a substitute for a reviewed, history-matched reservoir model. |
| **Pressure-transient well testing** | `engines/reservoir/well_test_analysis.py`: semilog drawdown, Horner buildup, Bourdet log derivative, and permeability/skin estimates. | Regime windows are heuristic diagnostics from derivative shape, not a physical inversion. Semilog results rely on a suitable radial-flow interval and the stated constant-rate/field-unit assumptions. |
| **Choke, tubing, and gas lift** | The ppes bridge exposes Gilbert choke pressure, critical ratio, sonic/subsonic gas flow, biaxial collapse, ballooning, piston effect, bending stress, gas-lift valve depth/open-close pressure, orifice sizing, and injection GLR. | These are individual book equations. They do not form a coupled well design, transient multiphase model, or standards-compliance check. Confirm equation applicability, geometry, material properties, and units for the specific use case. |
| **Minimum-curvature trajectory** | `engines/drilling/trajectory.py` computes directional survey coordinates; chart endpoints display plan and side views. | Requires valid measured depth, inclination, and azimuth columns. It is geometric survey integration, not a torque/drag, collision, or geomechanics analysis. |
| **Cartesian grid and charts** | `engines/geology/mesh.py` creates a Cartesian grid and computes cell/bulk volumes, including variable spacing; chart routes render grid extents. | The chart depicts a simple box, not a property model or geologic interpretation. The calculation does not create faults, stratigraphic surfaces, or unstructured grids. |
| **Production economics** | `engines/production/economic_analysis.py` calculates annual oil/gas revenue, annual OPEX, water disposal, straight-line depreciation, taxes, NPV, IRR, payback, and ROI. CAPEX is a year-zero outflow. | Inputs are annual volumes (oil/water bbl per year, gas Mscf per year), not daily rates. It is a simplified deterministic cash-flow model: no fiscal regime, royalties, inflation, abandonment, financing, or stochastic uncertainty is modeled unless represented externally in the inputs. |
| **LAS parsing and Archie OOIP** | LAS routes parse metadata/curves; the OOIP workflow estimates water saturation using Archie and applies a volumetric estimate. | LAS sessions are in-memory and expire after one hour. If no resistivity curve exists, OOIP uses a fixed 20 ohm-m fallback; `Bo=1.2` is fixed because no PVT is read from the LAS. Net pay is defined by a porosity cutoff. Treat OOIP as a screening estimate, not reserves. |
| **Facies classification** | `engines/petrophysics/facies.py` trains a Random Forest using gamma ray, resistivity, density, and porosity. | With no custom labeled training data, the API trains from only eight inline benchmark samples across four classes. This is not a broadly trained or field-validated classifier; custom representative labels are required for meaningful application. |

### Black-oil simulation

`POST /api/simulate/black-oil` invokes
`engines/reservoir/simulation/black_oil_simulator.py`. It accepts a Cartesian
grid, rock/fluid inputs, wells, initial state, and timesteps, with a 512-cell
API limit. The current implementation is explicitly a **simplified,
non-conservative surrogate**, not a validated full-field IMPES simulator:

- The pressure update is an ad-hoc linear surrogate and omits full
  compressibility, formation-volume-factor, and dissolved-gas coupling.
- Water and gas saturation updates are uncoupled; they do not enforce phase
  mass conservation or include capillary pressure.
- Well controls are simplified and do not use a coupled wellbore model or a
  validated Peaceman well index.
- Clipping saturation to physical bounds does not make the underlying update
  physically conservative.

Do not use the output as a design-grade or predictive reservoir forecast.

## Implemented modules without a supported API route

The following are source-code capabilities, not currently mounted calculation
endpoints. Their presence does not imply they are wired into the React app,
installed with all optional dependencies, or validated for operational use.
Some have direct unit/golden tests; use them only through the supported entry
points identified in the code and tests.

| Engine area | Existing modules / math | Current boundary or limitation |
|---|---|---|
| **Drilling** | `drilling/well_control.py`, `driller_sim.py`, `ecd.py`, `rop.py`, `rop_prediction.py`, `well_models.py`; well-control/hydraulics, equivalent circulating density, rate-of-penetration calculations, and related models. `trajectory.py` is API exposed. | Most drilling calculations do not have a FastAPI route. ROP prediction and well models are not wired into the current HTTP API; do not infer an end-to-end drilling simulator from the modules. |
| **Geology and geophysics** | `geology/digital_rock.py`, `geostatistics.py`, `model3d.py`, `nmr_analysis.py`, `petrophysics.py`, `reservoir_characterization.py`, `seismic_integration.py`, and `sensitivity.py`; mesh generation is API exposed. | Digital-rock, 3D, seismic, and characterization workflows are not exposed by the current API. Several rely on optional packages or prototype code; they are not a validated integrated static-model workflow. |
| **Petrophysics** | `petrophysics/porosity.py`, `las_reader.py`, and `facies.py`; the facies endpoint and LAS parsing workflows are API exposed. | The remaining helpers do not constitute a complete log-evaluation suite; facies model limitations are described above. |
| **Production and reserves** | `production/production_analysis.py`, `production_forecasting.py`, `production_optimization.py`, `reserves_evaluation.py`, `history_matching.py`, and `flow_history_matching.py`; `economic_analysis.py` is API exposed. | Forecasting, optimization, reserves, and history matching are not active API workflows. Their outputs are not equivalent to a reviewed reserves booking or calibrated production forecast. |
| **Analytics and prediction** | `analytics/advanced_analytics.py`, `ai_seismic.py`, `data_analytics.py`, `data_integration.py`, `event_detection.py`, `sequences.py`, `volve_eda.py`, and `prediction/ai_prediction.py`. | These are not mounted calculation endpoints. Some depend on optional machine-learning/visualization packages, and repository code includes experimental or incomplete paths. |
| **Modeling** | `modeling/geomechanics.py`, `static_modeling.py`, `thermal_modeling.py`, `uncertainty_analysis.py`, and `workflow_automation.py`. | These modules are not wired as active API workflows. Do not treat them as coupled geomechanical, static, thermal, uncertainty, or orchestration products without separate verification. |
| **Additional reservoir/simulation code** | `reservoir/reservoir_analysis.py`, `reservoir_engineering.py`, `reservoir_simulation.py`, plus simulation modules such as EOR, history matching, optimization, advanced simulation, and commercial-simulator integration. | These are not equivalent to active routes merely because classes or helper functions exist. Compositional and thermal API routes return HTTP 501; several simulation modules are scaffolds or require dependencies/interfaces not included in the running workflow. |

For the authoritative mounted-route inventory and exact schemas, see
[API_REFERENCE.md](API_REFERENCE.md). The route-level capability endpoint
`GET /api/v1/reservoir/capabilities` also documents a deliberately limited
catalog; it is not an exhaustive list of every API route or source module.
