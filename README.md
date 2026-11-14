# PetroLúmen

PetroLúmen is a React and FastAPI petroleum engineering workbench with a PyWebView desktop application. The desktop launcher serves the built React frontend from `dist/` through the embedded FastAPI process and passes its dynamically selected API port to the UI. The interface uses a dark-first navy/teal design system with an explicit light-theme option. The platform provides engineering workflows for PVT, drilling, geology, reservoir, production, petrophysics, and simulation, plus a LAS-to-OOIP workflow.

---

## Features

- **Well testing:** pressure drawdown and buildup analysis with permeability, skin, pressure estimates, and flow-regime diagnostics.
- **PVT and EOS:** reservoir-fluid correlations plus Peng–Robinson and SRK Z-factor calculations and a Wilson-K/Rachford–Rice screening flash.
- **Reservoir operations:** choke-flow, tubing-stress/movement, and gas-lift valve/orifice calculations.
- **Reservoir material balance and simulation:** backend Havlena–Odeh OOIP/OGIP estimation and a simplified black-oil solver; the solver's limitations are disclosed in its view.
- **Production economics:** annual oil/gas/water cash flows, taxes, water-disposal costs, NPV, IRR, payout, and ROI.
- **Production data:** authenticated CSV import, user-scoped well records, and a production overview dashboard.
- **Well-log workflows:** LAS parsing, Archie-based OOIP estimation, and Random Forest facies classification.
- **Existing engineering workbench:** drilling and well control, facilities, nodal analysis, decline, compressibility, scenario management, and saved-run comparison.

See [docs/API_REFERENCE.md](docs/API_REFERENCE.md) for all active HTTP routes and their Pydantic schemas, and [docs/ENGINE_CAPABILITIES.md](docs/ENGINE_CAPABILITIES.md) for calculation methods and limitations. Compositional and thermal simulation endpoints are currently stubs returning HTTP 501.

---

## For Users

### Windows desktop app

Download and extract the complete `release/desktop/PetroLumen` folder, then
run `PetroLumen.exe` inside it. Keep the folder intact; the executable depends
on the bundled files alongside it. The packaged app does not require Python or
Node.js. Windows still needs the Microsoft Edge WebView2 Runtime and .NET
Framework for the embedded browser and desktop window.

The app stores its local database, persistent authentication key, and dedicated
WebView profile in `%LOCALAPPDATA%\PetroLumen`.

## For Developers

### Build the Windows desktop package

From the repository root, install the frontend dependencies and run the
packaging script in PowerShell:

```powershell
npm ci
powershell -NoProfile -ExecutionPolicy Bypass -File .\build_exe.ps1
```

The script installs the backend, PyWebView, and PyInstaller dependencies,
builds the React frontend, and creates an onedir package at
`release\desktop\PetroLumen\`. Distribute the whole folder, not only
`PetroLumen.exe`. To skip work when dependencies or `dist/` are already
current, pass `-SkipDependencyInstall` and/or `-SkipFrontendBuild`.

The package stores user data and its WebView profile in
`%LOCALAPPDATA%\PetroLumen`; the generated `release/` folder is local build
output and is not committed to the repository.

## Quick Start

### 1. Server
```bash
cd backend && pip install -r requirements.txt && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 2. Desktop
```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install .\backend
.\.venv\Scripts\python.exe -m pip install -r .\frontend_desktop\requirements_desktop.txt
npm run build
.\PetroLumen.cmd
```
The desktop dependencies must be installed into the same local `.venv` that
`PetroLumen.cmd` prefers. In particular, install
`frontend_desktop\requirements_desktop.txt` there to provide PyWebView. Re-run
the two `pip install` commands after changing backend or desktop requirements.

The build produces the React assets in `dist/`, which the desktop app serves
locally; the UI and embedded API do not require a separate Node.js server at
runtime. The Windows installer copies the built `dist/` directory along with
the backend and desktop application, so build the frontend before running the
installer.
The Windows installer creates an isolated Python environment and installs these
dependencies automatically. `PetroLumen.cmd` then starts the embedded FastAPI
server and opens the PyWebView desktop client without requiring Node.js.
The desktop launcher creates an ephemeral authentication key when one is not
provided; standalone API deployments must configure `PETROLUMEN_SECRET_KEY`.

### 3. Tests
```bash
python -m pytest backend/tests -q
npm test
```
Latest verification: **246 backend tests passed (7 skipped), 83 frontend
Vitest tests passed, and all 92 engineering benchmarks passed.** The production
build uses `npm run build`.

### 4. Interactive API Documentation (Swagger)
Open your browser to:
```
http://127.0.0.1:8000/docs
```

---

## API and engineering references

The maintained inventory is [docs/API_REFERENCE.md](docs/API_REFERENCE.md).
It includes every OpenAPI operation mounted by the current FastAPI application,
including authenticated persistence and production routes, chart routes, and
the explicitly unimplemented simulation stubs. Calculation assumptions and
the status of backend engine modules are in
[docs/ENGINE_CAPABILITIES.md](docs/ENGINE_CAPABILITIES.md).

---

## What's Not Implemented

- `/api/simulate/compositional` → Returns HTTP 501 Not Implemented (compositional flow solver stubbed).
- `/api/simulate/thermal` → Returns HTTP 501 Not Implemented (thermal flow and heat-transfer solver stubbed).
- `black_oil_simulator.py` is a simplified surrogate model; see its docstring for limitations (physics is documented, not verified). Specifically, pressure is solved without full compressibility coupling, saturations are uncoupled without Darcy flux divergence or capillary pressure, and the supported simplified well controls do not constitute a fully coupled well model.
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
