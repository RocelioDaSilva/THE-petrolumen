# PetroLúmen

PetroLumen is a FastAPI-based reservoir engineering workbench with a PyWebView desktop client. It provides engineering endpoints for PVT, drilling, geology, reservoir, production, petrophysics, and simulation, plus a LAS-to-OOIP workflow.

---

## Quick Start

### 1. Server
```bash
cd backend && pip install -r requirements.txt && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 2. Desktop
```powershell
python -m pip install .\backend
python -m pip install -r frontend_desktop/requirements_desktop.txt
python frontend_desktop/desktop_app.py
```
The Windows installer creates an isolated Python environment and installs these
dependencies automatically. `PetroLumen.cmd` then starts the embedded FastAPI
server and opens the PyWebView desktop client without requiring Node.js.
The desktop launcher creates an ephemeral authentication key when one is not
provided; standalone API deployments must configure `PETROLUMEN_SECRET_KEY`.

### 3. Tests
```bash
cd backend && pytest tests/ -q
```

### 4. Interactive API Documentation (Swagger)
Open your browser to:
```
http://127.0.0.1:8000/docs
```

---

## What Works

The table below enumerates every endpoint currently returning 200 OK across the API surface, including the three new calculation engines (economics, facies classification, and material balance) alongside the LAS log parsing and workflow endpoints:

| Method | Path | Tag | Purpose |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/engine/drilling/trajectory` | Drilling | 3D wellbore trajectory calculation using the minimum curvature method. |
| `POST` | `/api/engine/drilling/trajectory/chart` | Drilling | Render trajectory profile chart as a base64-encoded PNG. |
| `POST` | `/api/engine/geology/grid` | Geology | 3D reservoir mesh generation, cell volume computation, and geometry verification. |
| `POST` | `/api/engine/geology/grid/chart` | Geology | Render 2D/3D reservoir grid cross-section chart as a base64-encoded PNG. |
| `POST` | `/api/engine/petrophysics/facies/classify` | Petrophysics | Lithofacies classification from well log curves (gamma, resistivity, density, porosity) using Random Forest. |
| `POST` | `/api/engine/production/economics` | Production | Field production economic evaluation calculating discounted cash flows, NPV, IRR, payout time, and fiscal sensitivities. |
| `POST` | `/api/engine/pvt/eos` | PVT | Peng-Robinson equation of state solver computing natural gas Z-factors and compressibility. |
| `POST` | `/api/engine/pvt/eos/chart` | PVT | Render Z-factor vs pressure isothermal curve chart as a base64-encoded PNG. |
| `POST` | `/api/engine/pvt/mbal` | PVT | Havlena-Odeh material balance analysis, OOIP/OGIP estimation, and drive indices (water, gas cap, solution gas). |
| `POST` | `/api/engine/reservoir/compressibility/rock` | Reservoir | Newman's sandstone/limestone pore-volume compressibility, with validity-range reporting. |
| `POST` | `/api/engine/reservoir/compressibility/gas` | Reservoir | Gas isothermal compressibility and Z-factor pressure derivative at fixed temperature. |
| `POST` | `/api/engine/reservoir/compressibility/total` | Reservoir | Phase-weighted total compressibility including rock, oil, water, and gas contributions. |
| `POST` | `/api/engine/reservoir/nodal` | Reservoir | Nodal analysis solver determining operating point intersection between Vogel IPR and TPR curves. |
| `POST` | `/api/engine/reservoir/nodal/chart` | Reservoir | Render Nodal analysis IPR/TPR intersection curve chart as a base64-encoded PNG. |
| `POST` | `/api/petrophysics/las/parse` | Petrophysics | Ingest and parse wireline log `.las` files to extract well metadata, curve arrays, and summary statistics. |
| `POST` | `/api/simulate/black-oil` | Simulation | 3D black-oil surrogate simulation running pressure and saturation timesteps across an uncoupled grid. |
| `GET` | `/health` | General | System health check and API version reporting. |

---

## What's Not Implemented

- `/api/simulate/compositional` → Returns HTTP 501 Not Implemented (compositional flow solver stubbed).
- `/api/simulate/thermal` → Returns HTTP 501 Not Implemented (thermal flow and heat-transfer solver stubbed).
- `black_oil_simulator.py` is a toy model; see its docstring for the limitations (physics is documented, not verified). Specifically, pressure is solved via an ad-hoc linear surrogate without true compressibility coupling, saturations are uncoupled without Darcy flux divergence or capillary pressure, and well conditions (`_apply_well_conditions`) are not implemented.
- Authenticated local accounts and saved simulation results are available; see
  [docs/PERSISTENCE.md](docs/PERSISTENCE.md) for standalone API configuration.

The reservoir calculation package is being expanded incrementally under
`backend/app/engines/reservoir/`; see [backend/README.md](backend/README.md)
for the active-engine versus scaffold distinction, units, and new
compressibility endpoints.

## Product scope

PetroLúmen is an engineering calculation and technical decision-support
workbench. Its core is transparent calculations, scenario inputs, engineering
workflows, and explainable results. It is not an ERP, a corporate accounting
system, a regulator's compliance certification tool, or an autonomous
engineering decision-maker. Simulation capabilities are disclosed with their
limits and should not be represented as equivalent to validated commercial
full-field simulators.

---

## Screenshots

### 3D Geology Grid
![chart](docs/screenshots/placeholder.png)
*Caption: 3D geology grid*

### Z-Factor vs Pressure
![chart](docs/screenshots/placeholder.png)
*Caption: z-factor vs pressure*

### IPR/TPR Nodal Intersection
![chart](docs/screenshots/placeholder.png)
*Caption: IPR/TPR nodal intersection*
