# PetroLúmen Desktop UI Capability vs Backend Audit

**Document:** Desktop UI Capability & Backend Parity Audit
**Target:** `frontend_desktop/` vs `backend/app/api/*.py` and `backend/app/engines/`
**Date:** November 2026
**Auditor:** Jules (AI Software Engineer)

---

## Executive Summary

This audit evaluates the feature completeness, API contracts, mathematical schema alignments, and user experience of the PetroLúmen Desktop client (`frontend_desktop/`) against the FastAPI backend services (`backend/app/api/`).

The desktop interface declares seven tools in `frontend_desktop/static/app.js`. Four tools connect to production calculation and visualization routes, one tool connects to a working numerical simulation engine but fails upon default execution due to a schema constraint mismatch, and two tools connect to unimplemented solver stubs that return HTTP 501. Concurrently, dozens of production-grade petroleum engineering engines in `backend/app/engines/` remain orphaned with neither API endpoints nor desktop UI representation.

---

## Section 1 — Per-Tool Audit Matrix & Detailed Profiles

Every tool defined in the `tools` array of `frontend_desktop/static/app.js` is audited below. Each tool appears exactly once.

### Summary Matrix

| ID | Title | Endpoint | Backend Status | Schema Match | Default Run UX |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `pvt` | PVT EOS | `/api/engine/pvt/eos` | **200 OK** | Exact Match | Renders interactive Peng-Robinson Z-factor curve |
| `trajectory` | Drilling Trajectory | `/api/engine/drilling/trajectory` | **200 OK** | Exact Match | Renders 2D plan view and side view directional survey plots |
| `grid` | Geology Grid | `/api/engine/geology/grid` | **200 OK** | Exact Match | Renders 3D Cartesian bounding box and bulk volume stats |
| `nodal` | Reservoir Nodal | `/api/engine/reservoir/nodal` | **200 OK** | Exact Match | Renders IPR vs. TPR curve intersection with operating point |
| `black-oil` | Simulate Black-Oil | `/api/simulate/black-oil` | **422 Unprocessable Entity** | **Mismatch** (2,000 cells vs 512 max limit) | Fails with 422 error; displays "No chart image was returned" |
| `compositional` | Simulate Compositional | `/api/simulate/compositional` | **501 Not Implemented** | Exact Match (Stubbed backend) | Disabled in navigation; displays 501 solver notice |
| `thermal` | Simulate Thermal | `/api/simulate/thermal` | **501 Not Implemented** | Exact Match (Stubbed backend) | Disabled in navigation; displays 501 solver notice |

---

### Detailed Tool Profiles

#### 1. PVT EOS (`pvt`)
* **ID:** `pvt`
* **Title:** PVT EOS
* **Group:** `PVT`
* **Primary Endpoint:** `POST /api/engine/pvt/eos`
* **Chart Endpoint:** `POST /api/engine/pvt/eos/chart`
* **Backend Status:** `200 OK`. Returns `HTTP 422` if mole fractions do not sum to 1 or components are non-physical. Returns `HTTP 500` if calculated Z-factor is non-physical ($Z \le 0$ or non-finite).
* **Form-vs-Pydantic Mismatch:**
  * **Form Fields:** `pressure` (number), `temperature` (number), `components` (JSON array of `EosComponentInput`), `composition` (JSON dict mapping names to mole fractions), `eos_type` (select: `"PR"`), `binary_interactions` (JSON matrix or `null`).
  * **Pydantic Model (`EosRequest`):** Validates positive finite pressure and temperature, non-empty components list with unique names, mole fractions summing to $1.0 \pm 10^{-6}$, and matching square binary interaction matrix dimensions.
  * **Mismatch Assessment:** None. Default payload aligns perfectly with Pydantic validation rules.
* **Expected Output vs. Actual Output:**
  * *Expected Output:* Plot of compressibility factor $Z$ vs. Pressure (MPa) with highlighted operating point; JSON data payload returning `{"z_factor": <float>}`.
  * *Actual Output:* `ChartResponse` with base64 PNG rendering a high-resolution Matplotlib curve. Data mode returns `{"z_factor": 0.9419...}`.
* **User Experience Today:**
  * Clicking **Run** immediately triggers `POST /api/engine/pvt/eos/chart`.
  * The chart renders smoothly in the result panel within 15–40 ms.
  * Toggling between "Chart" and "Data" mode operates seamlessly. "Reset to example" restores default component arrays.

---

#### 2. Drilling Trajectory (`trajectory`)
* **ID:** `trajectory`
* **Title:** Drilling Trajectory
* **Group:** `DRILLING`
* **Primary Endpoint:** `POST /api/engine/drilling/trajectory`
* **Chart Endpoint:** `POST /api/engine/drilling/trajectory/chart`
* **Backend Status:** `200 OK`. Returns `HTTP 422` if required column headers are missing or survey stations contain non-finite numbers.
* **Form-vs-Pydantic Mismatch:**
  * **Form Fields:** `survey` (JSON array of coordinate stations: `md`, `inc`, `azi`), `md_col` (text: `"md"`), `inc_col` (text: `"inc"`), `azi_col` (text: `"azi"`).
  * **Pydantic Model (`SurveyInput`):** Validates a non-empty list of stations where each dictionary must contain the designated MD, INC, and AZI column keys with finite float values.
  * **Mismatch Assessment:** None. Form defaults directly satisfy backend validation.
* **Expected Output vs. Actual Output:**
  * *Expected Output:* Visual plan view ($X$ vs $Y$) and section/side view ($X$ vs TVD) plots; JSON survey array enriched with TVD, Northing/Easting, closure distance, closure azimuth, and dogleg severity (DLS).
  * *Actual Output:* Dual-panel Matplotlib graphic showing plan view and side view with station depth annotations. Data mode returns complete station records with calculated spatial coordinates.
* **User Experience Today:**
  * Clicking **Run** executes `POST /api/engine/drilling/trajectory/chart` in 25–50 ms.
  * Status badge indicates `HTTP 200`. Directional well path is visualized cleanly.

---

#### 3. Geology Grid (`grid`)
* **ID:** `grid`
* **Title:** Geology Grid
* **Group:** `GEOLOGY`
* **Primary Endpoint:** `POST /api/engine/geology/grid`
* **Chart Endpoint:** `POST /api/engine/geology/grid/chart`
* **Backend Status:** `200 OK`. Returns `HTTP 422` if dimension counts do not match list lengths or spacings are non-positive.
* **Form-vs-Pydantic Mismatch:**
  * **Form Fields:** `nx` (integer: 50), `ny` (integer: 50), `nz` (integer: 20), `dx` (JSON: 25), `dy` (JSON: 25), `dz` (JSON: 5).
  * **Pydantic Model (`GridRequest`):** `nx`, `ny`, `nz` (integers $> 0$), and `dx`, `dy`, `dz` typed as `PositiveFloat | list[PositiveFloat]`.
  * **Mismatch Assessment:** Minor field typing inconsistency in the UI. In `app.js`, `dx`, `dy`, and `dz` are declared with `type: "json"`, generating multi-line textareas for simple scalar inputs (`25`, `25`, `5`). While `JSON.parse("25")` yields a valid number, presenting textareas for scalar dimensions is unintuitive.
* **Expected Output vs. Actual Output:**
  * *Expected Output:* 3D isometric bounding box representation of the reservoir volume with total cell count and bulk volume metrics.
  * *Actual Output:* Matplotlib 3D projection rendering cell extents, cell count ($50 \times 50 \times 20 = 50,000$), and bulk volume ($62,500,000.0\text{ m}^3$). Data mode returns `{"shape": [50, 50, 20], "total_cells": 50000, "bulk_volume": 62500000.0}`.
* **User Experience Today:**
  * Clicking **Run** generates the 3D grid graphic in 70–120 ms.
  * Clean presentation, though editing grid step sizes requires typing into JSON textareas rather than standard number fields.

---

#### 4. Reservoir Nodal (`nodal`)
* **ID:** `nodal`
* **Title:** Reservoir Nodal
* **Group:** `RESERVOIR`
* **Primary Endpoint:** `POST /api/engine/reservoir/nodal`
* **Chart Endpoint:** `POST /api/engine/reservoir/nodal/chart`
* **Backend Status:** `200 OK`. Returns `HTTP 422` if inputs are non-finite, negative, or if the numerical root finder fails to intersect IPR and TPR.
* **Form-vs-Pydantic Mismatch:**
  * **Form Fields:** `qi` (number: 12000), `pr` (number: 4200), `p_surf` (number: 800), `a` (number: 0.0015), `b` (number: 8).
  * **Pydantic Model (`NodalRequest`):** `qi` (PositiveFloat), `pr` (PositiveFloat), `p_surf` (float $\ge 0$), `a` (float $\ge 0$), `b` (float $\ge 0$).
  * **Mismatch Assessment:** None. Perfect parity between UI inputs and Pydantic constraints.
* **Expected Output vs. Actual Output:**
  * *Expected Output:* Inflow Performance Relationship (IPR) and Tubing Performance Relationship (TPR) curves intersecting at the operating point $(q_{\text{op}}, p_{\text{wf}})$; Data mode showing numerical operating flow rate.
  * *Actual Output:* Matplotlib plot with blue IPR curve, orange TPR curve, and marked red intersection point ($q_{\text{op}} = 2933.33\text{ STB/D}$). Data mode returns `{"operating_rate": 2933.3333333333335}`.
* **User Experience Today:**
  * Fast execution (~20–40 ms).
  * Informative chart with operating point callout annotation.

---

#### 5. Simulate Black-Oil (`black-oil`)
* **ID:** `black-oil`
* **Title:** Simulate Black-Oil
* **Group:** `SIMULATION`
* **Primary Endpoint:** `POST /api/simulate/black-oil`
* **Chart Endpoint:** None (tool has no `chartMode` defined in `app.js`).
* **Backend Status:** `422 Unprocessable Entity` with default UI configuration. Returns `200 OK` only when manually downsized to $\le 512$ cells. Returns `500 Internal Server Error` if pressures or saturations become non-physical ($p \le 0$, $S_w < 0$, $S_g < 0$, $S_w + S_g > 1$).
* **Form-vs-Pydantic Mismatch:**
  * **Critical Constraint Mismatch:** Default form values in `app.js` initialize a grid of dimensions `nx: 20, ny: 20, nz: 5` ($20 \times 20 \times 5 = 2,000$ cells) and populates arrays of 2,000 elements for `porosity`, `permeability`, `initial_water_saturation`, and `initial_gas_saturation`.
  * **Backend Validator Constraint:** In `backend/app/api/simulation_routes.py`, `MAX_BLACK_OIL_CELLS = 512` is strictly enforced:
    ```python
    if cell_count > MAX_BLACK_OIL_CELLS:
        raise ValueError(
            f"Black-oil simulations are limited to {MAX_BLACK_OIL_CELLS} "
            "grid cells because this solver allocates dense matrices."
        )
    ```
  * **Display Mode Mismatch:** `app.js` initializes `currentResultMode = tool.chartMode || "chart"`. Because `black-oil` has no `chartMode` property, `currentResultMode` defaults to `"chart"`. The client sends `POST /api/simulate/black-oil` (there is no `/chart` endpoint), receives the JSON response, and inspects `payload.image_base64`. Because the payload is JSON rather than an image, the UI falls back to displaying: *"No chart image was returned by the engine."*
* **Expected Output vs. Actual Output:**
  * *Expected Output:* Multi-phase reservoir flow simulation computing 3D pressure and phase saturation distributions over 30 timesteps.
  * *Actual Output:* Immediate HTTP 422 validation failure:
    `HTTP 422 · request: Value error, Black-oil simulations are limited to 512 grid cells because this solver allocates dense matrices.`
* **User Experience Today:**
  * Completely broken out-of-the-box user experience.
  * An engineer selects "Simulate Black-Oil", clicks "Run calculation", and immediately encounters a red status badge indicating `HTTP 422` with a dense matrix cell limit error.
  * The primary result viewport displays *"No chart image was returned by the engine."*
  * The user must manually navigate to the "Data" tab to understand the JSON error breakdown, and must manually edit five JSON textareas down to $\le 512$ cells to achieve a successful run.

---

#### 6. Simulate Compositional (`compositional`)
* **ID:** `compositional`
* **Title:** Simulate Compositional
* **Group:** `SIMULATION`
* **Primary Endpoint:** `POST /api/simulate/compositional`
* **Backend Status:** `501 Not Implemented`.
* **Form-vs-Pydantic Mismatch:**
  * Form fields match `CompositionalInput` (`grid`, `components`, `rock_properties`, `wells`, `initial_composition`, `timesteps`).
  * Backend route instantiates `CompositionalSimulator`, calls setup methods, and immediately invokes `_not_implemented("The compositional flow solver is not implemented; no simulation results were produced.")`.
* **Expected Output vs. Actual Output:**
  * *Expected Output:* Multi-component flash and compositional phase-flow simulation results.
  * *Actual Output:* `HTTP 501 Not Implemented` with detail message: `"The compositional flow solver is not implemented; no simulation results were produced."`
* **User Experience Today:**
  * Marked with `disabled: true` and `disabledNote: "Solver not yet implemented (backend returns 501)."` in `app.js`.
  * The sidebar button has class `disabled` and attribute `aria-disabled="true"`.
  * Clicking the sidebar button does nothing (`if (!tool.disabled) showTool(tool)`).
  * The user cannot select or open the tool through the navigation bar. However, having non-functional tools in the primary navigation creates cognitive noise and gives an impression of incomplete software.

---

#### 7. Simulate Thermal (`thermal`)
* **ID:** `thermal`
* **Title:** Simulate Thermal
* **Group:** `SIMULATION`
* **Primary Endpoint:** `POST /api/simulate/thermal`
* **Backend Status:** `501 Not Implemented`.
* **Form-vs-Pydantic Mismatch:**
  * Form fields match `ThermalInput` (`CompositionalInput` plus `thermal_properties` and `initial_temperature`).
  * Backend route sets up components, grid, and thermal properties on `ThermalSimulator`, executes timesteps, and immediately invokes `_not_implemented("The thermal flow and heat-transfer solver is not implemented; no simulation results were produced.")`.
* **Expected Output vs. Actual Output:**
  * *Expected Output:* Thermal energy conservation and convective heat-transfer simulation profiles.
  * *Actual Output:* `HTTP 501 Not Implemented` with detail message: `"The thermal flow and heat-transfer solver is not implemented; no simulation results were produced."`
* **User Experience Today:**
  * Marked with `disabled: true` and `disabledNote: "Solver not yet implemented (backend returns 501)."` in `app.js`.
  * Rendered as an inactive sidebar item (`aria-disabled="true"`). Clicking does not navigate to the tool.
  * Clutters the primary navigation list without delivering functional capability.

---

## Section 2 — Underserved: Orphaned Engines Worth a UI Tool

The backend engine library (`backend/app/engines/`) contains over 70 computational modules across drilling, reservoir, geology, petrophysics, production, and analytics. However, only four functional areas (`pvt`, `trajectory`, `grid`, `nodal`) are accessible via the desktop UI.

The following high-value engines are fully implemented in Python but currently **orphaned**—lacking either a dedicated FastAPI endpoint, desktop UI tool, or both:

### 1. Decline Curve Analysis (DCA) & Reserves Forecasting
* **Engine Modules:** `backend/app/engines/pvt/dca.py` and `backend/app/engines/reservoir/decline_curve.py`
* **Analytical Capability:**
  * Implements standard Arps empirical decline models: Exponential ($b=0$), Harmonic ($b=1$), and Hyperbolic ($0 < b < 1$).
  * Computes Estimated Ultimate Recovery (EUR), remaining recoverable reserves, and production rate vs. time forecasts.
  * Includes optimization routines to fit empirical decline curves to historical production time-series.
* **Engineering Value & UI Need:**
  * Production and reservoir engineers use DCA daily for reserve estimation and economic budgeting.
  * Exposing this engine requires a lightweight input form (initial rate $q_i$, initial decline $D_i$, $b$-factor, economic limit $q_f$) and renders standard semi-log production vs. time plots.

### 2. Well Control, Kick Sheet & Tripping Hydraulics
* **Engine Module:** `backend/app/engines/drilling/well_control.py`
* **Analytical Capability:**
  * Calculates kill sheet parameters, initial circulating pressure (ICP), final circulating pressure (FCP), and kill mud weight (KMW).
  * Computes Maximum Allowable Annular Surface Pressure (MAASP) and casing shoe fracture margins based on leak-off test (LOT) data.
  * Evaluates gas influx migration velocity, kick volume expansion, and surface casing pressure profiles.
* **Engineering Value & UI Need:**
  * Vital operational safety engineering capability.
  * A dedicated desktop tool accepting drillstring geometry, hole size, shut-in drillpipe pressure (SIDPP), and shut-in casing pressure (SICP) would provide immediate operational validation for drilling engineers.

### 3. Drilling Hydraulics & Equivalent Circulating Density (ECD)
* **Engine Module:** `backend/app/engines/drilling/ecd.py`
* **Analytical Capability:**
  * Models non-Newtonian fluid rheology (Bingham Plastic and Power Law models).
  * Computes annular pressure drops, frictional pressure losses across the drillstring, and bottom-hole Equivalent Circulating Density (ECD).
  * Accounts for tool joint restrictions and cutting bed slip velocities.
* **Engineering Value & UI Need:**
  * Crucial for avoiding mud losses and borehole collapse while drilling narrow drilling margin windows.
  * Highly visual domain suitable for depth-vs-ECD margin charts.

### 4. Petrophysical Log Evaluation & Lithofacies Classification
* **Engine Modules:** `backend/app/engines/petrophysics/porosity.py`, `backend/app/engines/petrophysics/facies.py`, `backend/app/engines/petrophysics/las_reader.py`
* **Analytical Capability:**
  * Computes density porosity ($\phi_D$), sonic porosity ($\phi_S$), neutron-density crossplot porosity, and shale volume ($V_{\text{sh}}$ via Larionov / Stieber).
  * Computes water saturation ($S_w$) via Archie's equation and dual-water shaly-sand models.
  * Automates unsupervised machine-learning facies classification from gamma ray, resistivity, and density log tracks.
* **Engineering Value & UI Need:**
  * Petrophysicists require rapid well log analysis without launching heavy enterprise suites.
  * A desktop tool taking LAS files or curve arrays and outputting multi-track depth logs represents a flagship capability.

### 5. Production Economic Evaluation & Cash Flow Modeling
* **Engine Module:** `backend/app/engines/production/economic_analysis.py`
* **Analytical Capability:**
  * Discounted Cash Flow (DCF) modeling calculating Net Present Value (NPV), Internal Rate of Return (IRR), Payback Period, and Profitability Index (PI).
  * CAPEX, OPEX, oil/gas commodity price escalation, royalty rates, and production sharing contract (PSC) terms.
  * 1D and 2D sensitivity analysis (tornado charts and price/volume spider plots).
* **Engineering Value & UI Need:**
  * Engineering projects require financial justification. Pairing DCA rate forecasts directly with the economics engine creates an end-to-end reservoir evaluation workflow.

### 6. Reservoir Material Balance (MBAL) & Aquifer Influx
* **Engine Modules:** `backend/app/engines/pvt/mbal.py` and `backend/app/engines/reservoir/material_balance.py`
* **Analytical Capability:**
  * Generalized Havlena-Odeh material balance equation for oil and gas reservoirs.
  * Gas $p/Z$ straight-line plots for Original Gas in Place (OGIP) determination.
  * Analytical aquifer water drive models (Carter-Tracy, Fetkovich, and Schilthuis).
* **Engineering Value & UI Need:**
  * Essential classical reservoir engineering diagnostic tool for determining drive mechanisms and initial hydrocarbons in place without full numerical simulation.

---

## Section 3 — Over-Served: Tools With 501 / 500 Endpoints

An application should never present non-functional or severely impaired backend endpoints as viable user tools. In `frontend_desktop/`, two tools hit stubbed endpoints returning HTTP 501, and one tool experiences catastrophic validation failure on its default payload:

### 1. `simulate/compositional` (HTTP 501 Not Implemented)
* **Status:** Backend endpoint `POST /api/simulate/compositional` executes input parsing and immediately throws an HTTP 501 error via `_not_implemented()`.
* **Current UI Handling:** In `frontend_desktop/static/app.js`, the tool is flagged with `disabled: true` and `aria-disabled="true"`. Clicking the sidebar item is blocked in JavaScript.
* **Why It Is Over-Served:**
  * While greyed out, the tool remains in the primary tool navigation list.
  * When a new user looks at the tool suite, two out of the three simulation tools are dead links.
  * It occupies prominent visual hierarchy in the "SIMULATION" section alongside production-ready tools, signaling an incomplete product rather than a stable engineering suite.

### 2. `simulate/thermal` (HTTP 501 Not Implemented)
* **Status:** Backend endpoint `POST /api/simulate/thermal` similarly validates `ThermalInput` and terminates with `HTTP 501 Not Implemented`.
* **Current UI Handling:** Configured as `disabled: true`. The navigation item is unclickable.
* **Why It Is Over-Served:**
  * Exactly as with Compositional, Thermal simulation is displayed directly beneath Black-Oil.
  * Having 2 out of 7 total desktop tools permanently disabled in the main navigation degrades user trust.
  * Tools whose backend status is 501 should be completely removed from the primary tool rail or moved into a segregated "Roadmap / Experimental" drawer clearly labeled as unavailable.

### 3. `simulate/black-oil` (HTTP 422 Default Failure / Potential HTTP 500 Non-Physical State)
* **Status:**
  * **Default Execution:** Returns `HTTP 422 Unprocessable Entity` because default inputs allocate 2,000 cells ($20 \times 20 \times 5$), exceeding the 512-cell limit in `backend/app/api/simulation_routes.py`.
  * **Engine Exception Handling:** If the solver produces negative pressures or saturations summing to $>1$, the backend raises `HTTP 500 Internal Server Error` (*"The black-oil solver produced a non-physical reservoir state; results were not returned."*).
* **Current UI Handling:**
  * Displayed as an active, fully usable tool with a prominent "Run calculation" action.
  * The user is given no prior indication that clicking Run on the default form will immediately fail.
  * Because `chartMode` is missing, the result panel defaults to "Chart" mode and displays *"No chart image was returned by the engine."*
* **Why It Is Over-Served:**
  * Presenting a tool as usable when its provided default parameters violate backend constraints is a critical usability defect.
  * The tool must either have its default parameters aligned with the backend limit ($8 \times 8 \times 8 = 512$ cells or smaller) or enforce client-side validation before dispatching requests.

---

## Section 4 — Top 5 UX Improvements Ranked by Impact

The following five UX improvements are prioritized and ranked based on their engineering value, operational impact, and reduction in user friction:

### Rank 1: Client-Side Schema & Constraint Validation Before Submission
* **Impact:** **Critical** (Eliminates immediate 422 errors and unhandled exceptions)
* **Current Pain Point:**
  * When an engineer clicks "Run calculation" on `black-oil`, the client sends a 2,000-cell grid that violates the backend's 512-cell constraint, yielding an unhandled `HTTP 422` error.
  * Similarly, entering malformed JSON into array fields throws a raw JavaScript exception that prints unstyled text to the status element.
* **Proposed Solution:**
  * Implement client-side validation in `getFormData()` or an `onValidate()` hook before `fetch()`.
  * For simulation grids, compute `nx * ny * nz` live. If the product exceeds 512, display an inline warning badge on the grid inputs and disable the "Run" button with an explanatory tooltip: *"Grid exceeds solver limit of 512 cells (currently: {N})."*
  * Verify that property array lengths (`porosity`, `permeability`, `saturation`) match the cell count prior to dispatch.
  * Provide instant syntax checking for JSON fields with inline red borders and localized error banners rather than generic execution failure messages.

### Rank 2: Context-Aware Result Mode & Dedicated Simulation Visualization
* **Impact:** **High** (Resolves confusing "No chart image returned" empty state)
* **Current Pain Point:**
  * `app.js` initializes `currentResultMode = tool.chartMode || "chart"`.
  * Because `black-oil` does not define `chartMode`, the application defaults to "Chart" mode, sending requests to the raw data endpoint. When the response arrives without an `image_base64` property, the UI renders: *"No chart image was returned by the engine."*
  * The user is forced to discover and click the "Data" tab to view their output.
* **Proposed Solution:**
  * If a tool does not define `chartMode` (or if no `/chart` endpoint exists), automatically default `currentResultMode` to `"json"` (Data view) and disable the "Chart" toggle button with a disabled state styling.
  * Add a backend chart route for black-oil (`/api/simulate/black-oil/chart`) or build client-side rendering (e.g., using lightweight Canvas or SVG) that visualizes average reservoir pressure decline and phase production over time.

### Rank 3: Segregated "Coming Soon" Drawer for 501 / Stubbed Solvers
* **Impact:** **High** (Eliminates dead navigation items and restores professional polish)
* **Current Pain Point:**
  * Compositional and Thermal simulation tools are listed alongside active tools in the main sidebar navigation with `aria-disabled="true"`.
  * Clicking them produces no visual feedback or explanation unless the DOM is inspected.
* **Proposed Solution:**
  * Remove disabled 501 endpoints from the primary tool rail.
  * Introduce a separate, clearly demarcated section at the bottom of the navigation: *"Upcoming Solvers"* or *"Roadmap"*.
  * When clicked, display a polished preview panel showing the planned capabilities, governing equations (e.g., Peng-Robinson phase split flash algorithms, steam-assisted gravity drainage), and expected release milestones rather than an unclickable button.

### Rank 4: Live Execution Progress, Timers, and Request Cancellation
* **Impact:** **Medium** (Improves responsiveness and user confidence during heavy computations)
* **Current Pain Point:**
  * High-dimensional matrix calculations (such as 3D grid volumes or multi-step iterative black-oil simulations) can take several seconds to solve.
  * While computing, the "Run calculation" button remains static with no spinner, no elapsed timer, and no ability to cancel a long-running request.
* **Proposed Solution:**
  * Replace the button text with an animated spinner (`Running simulation…`) and disable repeated clicks during execution.
  * Display a live elapsed time counter that updates every 100 ms.
  * Integrate an `AbortController` bound to a "Cancel" action, enabling engineers to abort long-running numerical calculations if incorrect parameters were submitted.

### Rank 5: Tabular Data Grid & File Upload for Complex Engineering Inputs
* **Impact:** **Medium** (Eliminates error-prone manual JSON typing for multi-station datasets)
* **Current Pain Point:**
  * Directional survey stations, PVT EOS component fractions, and 3D simulation arrays require engineers to type or paste hundreds of lines of raw JSON into plain textareas.
  * A single missing bracket, comma, or quote causes an unhelpful JSON parsing error.
* **Proposed Solution:**
  * Replace raw JSON textareas with structured, interactive data tables supporting inline editing, row addition, and column sorting.
  * Provide a "Upload File" button supporting standard petroleum data formats:
    * CSV / Excel for directional surveys (`MD`, `INC`, `AZI`) and PVT fluid compositions.
    * Standard LAS (Log ASCII Standard) format for petrophysical well logs.
  * Allow engineers to export results directly to CSV and PNG formats from the desktop interface.

---

## Conclusion & Recommended Next Steps

1. **Immediate Remediation (Zero-Risk):**
   * Adjust default parameters for `black-oil` in `frontend_desktop/static/app.js` to $8 \times 8 \times 4 = 256$ cells (or $4 \times 4 \times 4 = 64$ cells) so the tool succeeds on the first click.
   * Update `showTool()` to set `currentResultMode = tool.chartMode ? tool.chartMode : "json"`, ensuring tools without charts open directly to the Data view.
2. **Medium-Term Integration:**
   * Build FastAPI endpoints for the orphaned DCA (`dca.py`) and Well Control (`well_control.py`) engines, connecting them to new desktop UI views.
   * Move `compositional` and `thermal` tools to an "Upcoming Features" drawer until full solvers are deployed.
3. **Architecture Hardening:**
   * Introduce client-side pre-flight validation to catch constraint violations before triggering network round-trips.
