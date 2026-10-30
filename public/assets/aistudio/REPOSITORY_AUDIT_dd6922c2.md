# PetroLúmen Repository Audit Report

**Date:** October 2024
**Auditor:** Jules (AI Software Engineer)
**Target Repository:** PetroLúmen Reservoir Engineering Application

---

## 1. Executive Summary

### 1.1. Overview
PetroLúmen is a comprehensive reservoir engineering application combining a desktop client built with **Next.js 15**, **React 19**, **Tauri v2**, and **TypeScript** with a high-performance backend powered by **Python 3.12** and **FastAPI**. The core computational and analytical domain logic resides in the `gaia_genesis` package, providing PVT correlations, 1D IMPES reservoir simulation, decline curve analysis (DCA), rate transient analysis (RTA), nodal analysis, material balance, and AI-based production forecasting.

This audit presents an exhaustive evaluation of the entire repository across architecture, security, concurrency, testing, UI/UX resilience, performance, and maintainability.

### 1.2. Key Audit Highlights
* **Backend Test Suite Health:** Excellent baseline. **177 pytest unit and integration tests** pass cleanly.
* **Frontend Test Suite Health:** Functional baseline with **6 passing Vitest unit tests**, though component-level and E2E test coverage remains lightweight.
* **Concurrency Architecture Risk:** Core service modules in `backend/main.py` and `backend/gaia_genesis/api_v1/endpoints/static_modeling_tools.py` utilize **shared global stateful instances** (`res_simulator`, `dca_analyzer`, `ai_predictor`, `static_model_analyzer`). Multi-user concurrent sessions will cause cross-talk or state pollution unless refactored to per-user or task-scoped resource managers.
* **Security & Authentication:** Robust JWT Bearer header-based authentication, bcrypt password hashing with work factor ≥ 12, and role-based access control (RBAC). Default secret warnings are active when default configuration is used.
* **Database & Migrations:** Clean SQLAlchemy ORM architecture with explicit Alembic migration paths, supporting both SQLite for local desktop development and PostgreSQL for enterprise deployments.

### 1.3. Audit Scorecard

| Area | Rating | Key Finding |
| :--- | :--- | :--- |
| **Backend Architecture** | 🟨 Moderate | Robust algorithms; relies on shared global state instances for simulation/DCA. |
| **Frontend Architecture** | 🟩 Good | Modern Next.js 15 + Tauri v2 setup; clean Zustand unit conversions. |
| **Security & Auth** | 🟩 Good | Header-based JWT, bcrypt hashing, clear secret warnings in `config.py`. |
| **Backend Testing** | 🟩 Good | 177 pytest tests passing; covers API endpoints, models, and core math. |
| **Frontend Testing** | 🟨 Moderate | 6 Vitest tests passing (`lib/utils.test.ts`); lacks component & E2E tests. |
| **Dependencies & Security** | 🟨 Moderate | Moderate esbuild advisory (`GHSA-67mh-4wv8-2f99`) in frontend; `bcrypt<4.0.0` pin for Passlib. |
| **Documentation & Onboarding** | 🟩 Excellent | Comprehensive `AGENTS.md`, `DEVELOPER_ONBOARDING.md`, `README.md`, and docs. |

---

## 2. Repository Structure & Monorepo Organization

### 2.1. Directory Structure Overview
```
/
├── backend/                  # FastAPI Application & Gaia Genesis Package
│   ├── alembic/              # DB Schema Migration Scripts
│   ├── gaia_genesis/         # Core Reservoir Engineering & Scientific Engine
│   │   ├── analytics/        # Seismic & ML Analytics
│   │   ├── api_v1/           # Modular REST API Endpoints & Schemas
│   │   ├── auth/             # Authentication Service Layer
│   │   ├── core/             # Database, Auth, and Data Uploader Managers
│   │   ├── prediction/       # Time Series & ML Prediction (Prophet, SVR, XGBoost)
│   │   ├── pvt.py            # Black Oil & Compositional PVT Engine
│   │   ├── flow_simulation.py# 1D IMPES Two-Phase Numerical Reservoir Simulator
│   │   ├── dca_advanced.py   # Advanced DCA Models (Arps, Duong, PLE, SEPD)
│   │   ├── rta.py            # Rate Transient Analysis & FMB
│   │   ├── nodal.py          # Nodal Analysis & Numerical Inflow/Outflow Solver
│   │   └── static_modeling.py# Kriging Interpolation & Geostatistical Modeling
│   ├── tests/                # Pytest Test Suite (177 tests)
│   ├── main.py               # FastAPI App Initialization & Handlers
│   └── config.py             # Pydantic Settings Configuration
├── petrolumen/               # Frontend Desktop Client (Next.js 15, Tauri v2)
│   ├── app/                  # Next.js App Router Pages & Layouts
│   ├── components/           # UI Components (shadcn/ui, Radix UI)
│   ├── hooks/                # Custom React Hooks
│   ├── lib/                  # Utilities & Global Unit Conversion (`units.ts`)
│   ├── stores/               # Zustand Global Stores (`unitStore.ts`, `appStore.ts`)
│   ├── src-tauri/            # Tauri Desktop Engine (Rust Config & Cargo)
│   └── src/                  # Legacy Pages/Components (`pvt-analysis.jsx`)
├── docs/                     # Project-Wide Documentation
├── possible feature calculation/ # Source/Draft Algorithms for Feature Integration
├── possible_improvements/    # Technical Debt & Issue Backlog Tracking
└── REPOSITORY_AUDIT.md       # Full Repository Audit Report (This Document)
```

### 2.2. Technology Stack & Environment

#### Backend:
* **Framework:** FastAPI 0.116.0 with Uvicorn 0.35.0
* **Language:** Python 3.12
* **ORM & Database:** SQLAlchemy 2.0.41, Alembic 1.16.3 (SQLite / PostgreSQL)
* **Scientific & ML Libraries:** NumPy 2.3.1, SciPy 1.16.0, Pandas 2.3.1, scikit-learn 1.5.2, XGBoost 3.0.2, Meta Prophet 1.3.0, PyVista 0.43.3, VTK 9.5.0, Lasio 0.30, Segyio 1.9.13
* **Logging & Auth:** structlog 25.5.0, Passlib 1.7.4, bcrypt 4.3.0, PyJWT 2.12.1

#### Frontend:
* **Framework:** Next.js 15.3.4 (React 19, App Router), Tauri 2.6.0
* **Language:** TypeScript 5.8.3
* **Styling & UI:** Tailwind CSS 4, Radix UI Primitives, Lucide Icons, Sonner Toasts
* **State Management:** Zustand 4.5.4 (`unitStore`, `appStore`)
* **Data Visualization & Export:** Recharts 3.0.2, jsPDF 4.2.1, html2canvas 1.4.1
* **Testing:** Vitest 2.0.5, React Testing Library 16.0.0

---

## 3. Backend Audit (`backend/`)

### 3.1. Concurrency & State Management
* **Finding:** Key stateful objects (`res_simulator`, `dca_analyzer`, `ai_predictor` in `main.py` and `static_model_analyzer` in `endpoints/static_modeling_tools.py`) are instantiated as **module-level singletons**.
* **Impact:** Concurrent API requests from multiple users modify the same simulator, grid setup, or DCA fitting parameters, resulting in race conditions and data bleeding across sessions.
* **Recommendation:**
  1. Refactor stateful analyzers to accept model parameters statelessly per-request.
  2. Implement an in-memory session/task cache keyed by `session_id` or `user_id` for interactive simulation workflows.

### 3.2. Core Engineering Logic Assessment

#### 1. PVT Properties Engine (`gaia_genesis/pvt.py`)
* **Correlations:** Standing, Glaso, Vasquez-Beggs, DAK (Dranchuk-Abou-Kassem) Z-factor solver, Hall-Yarborough.
* **Compositional EOS:** Peng-Robinson Equation of State (EOS) flash solver.
* **Quality:** Excellent convergence handling with custom fallback bounds and vectorized calculation support.

#### 2. Reservoir Flow Simulator (`gaia_genesis/flow_simulation.py`)
* **Numerical Method:** 1D two-phase (oil-water) IMPES (Implicit Pressure, Explicit Saturation) formulation.
* **Matrix Solver:** Thomas Algorithm for tridiagonal system solutions during implicit pressure updates.
* **Rock-Fluid Physics:** Brooks-Corey capillary pressure and Stone II relative permeability models.
* **Quality:** High mathematical integrity for 1D single/two-phase simulations; verified via `test_flow_simulation_dry_gas.py`.

#### 3. Decline Curve Analysis (`gaia_genesis/dca_advanced.py`)
* **Models:** Exponential, Hyperbolic, Harmonic (Arps), Duong, Power Law Exponential (PLE), Stretched Exponential Production Decline (SEPD).
* **Optimization:** `scipy.optimize.curve_fit` with custom parameter bounds.

#### 4. Rate Transient Analysis (`gaia_genesis/rta.py`) & Nodal Analysis (`gaia_genesis/nodal.py`)
* **RTA:** Flowing Material Balance (FMB) for gas reservoirs using normalized rate and pseudo-time.
* **Nodal:** Numerical inflow performance relationship (IPR) and tubing performance relationship (TPR) operating point intersection solver using `scipy.optimize.fsolve`.

#### 5. AI & Time-Series Forecasting (`gaia_genesis/prediction/`)
* **Models:** SVR, XGBoost Regressor with hyperparameter tuning, Meta Prophet time-series forecasting.
* **Compatibility:** Handled pandas modern Month End (`ME`) frequency alias to ensure clean execution under pandas 2.x.

### 3.3. Database Architecture & Migrations
* **ORM:** Clean SQLAlchemy 2.0 models in `backend/gaia_genesis/core/database_models.py`.
* **Migrations:** Alembic configured in `backend/alembic.ini` and `backend/alembic/env.py`. Database auto-migration is triggered during application startup in `main.py`.
* **Datatypes:** UUID primary keys and UTC-aware ISO-8601 datetimes ensure full compatibility with SQLite and PostgreSQL.

### 3.4. Logging & Error Handling
* **Logging:** Structured JSON logging implemented via `structlog`, binding `request_id` from custom middleware and `user_id` from authentication contexts.
* **Error Handling:** Global exception handler catches unhandled exceptions and formats standardized JSON error responses with HTTP status codes and trace identifiers.

---

## 4. Frontend Audit (`petrolumen/`)

### 4.1. Architecture & Dual-Router Setup
* **App Router (`app/`):** Primary routing system covering `/ai`, `/dca`, `/economics`, `/nodal`, `/pvt`, `/pvt-calculations`, `/reservoir`, `/rta`, `/simulation`, and `/visual-probe`.
* **Pages Router (`src/pages`):** Legacy route (`src/pages/pvt-analysis.jsx`) remains alongside App Router pages.
* **Recommendation:** Consolidate `src/pages` into the Next.js App Router (`app/`) to prevent duplicate bundles and routing confusion.

### 4.2. Unit Management & State Persistence
* **Global Unit System:** Controlled via `stores/unitStore.ts` using Zustand. Supported systems: **Field (US Customary)** and **Metric (SI)**.
* **Unit Utility (`lib/units.ts`):** Centralized unit conversion factors for pressure (psi ↔ bar / kPa), temperature (°F ↔ °C), flow rates (STB/d ↔ m³/d, Mscf/d ↔ m³/d), and volume (MMscf ↔ m³).
* **Store State:** `stores/appStore.ts` tracks active well selection, loaded datasets, and active analysis tools.

### 4.3. UI/UX Resilience & 4-State UI Compliance
* **Loading State:** Skeleton loaders (`components/ui/skeleton.tsx`) displayed during API fetches.
* **Empty State:** Clear informational callouts when no well data or calculations are loaded.
* **Error State:** User-friendly error message cards featuring explicit **Retry** buttons.
* **Success State:** Interactive charts (Recharts) and data summary cards with PDF export capability (`jspdf` + `html2canvas`).

---

## 5. Security, Governance & Compliance

### 5.1. Authentication & Token Security
* **Protocol:** Bearer JWT tokens sent via HTTP `Authorization` header.
* **Password Security:** Hashed via bcrypt with a work factor of 12.
* **Constraint Note:** Backend requirements enforce `bcrypt<4.0.0` to preserve Passlib 1.7.4 compatibility and avoid null-byte hash failures during execution.
* **RBAC:** Role checks enforced via FastAPI dependency `get_current_active_admin_user`.

### 5.2. Secret Management
* **Configuration:** Managed via Pydantic `BaseSettings` in `backend/config.py`.
* **Environment Files:** Reads from `.env`. Fallback default `SECRET_KEY` triggers startup warnings in `main.py` if unmodified in non-production environments.

### 5.3. Dependency Vulnerabilities
* **Frontend Advisory:** `pnpm audit` identifies a moderate severity advisory in `esbuild` (`<=0.24.2`, GHSA-67mh-4wv8-2f99) nested under `@vitejs/plugin-react`.
* **Action:** Upgrade `vite` / `@vitejs/plugin-react` or apply `pnpm.overrides` for `esbuild` to version `>=0.25.0`.

---

## 6. Testing & Quality Assurance

### 6.1. Test Coverage Summary
* **Backend Pytest Suite:** **177 passed**, 0 failed (Execution time: ~90s).
  * `test_ai_forecasting.py`: Meta Prophet time-series verification.
  * `test_analysis_endpoints.py`: DCA and RTA endpoint logic.
  * `test_auth_manager.py`: User registration, authentication, token verification.
  * `test_database_manager.py`: CRUD operations on wells and production data.
  * `test_flow_simulation_dry_gas.py`: 1D dry gas IMPES solver validation.
  * `test_gaia_pvt_endpoints.py`: Comprehensive PVT calculations and EOS flash testing.
  * `test_integrated_logic.py`: Ordinary Kriging, spatial statistics, rock physics.
* **Frontend Vitest Suite:** **6 passed**, 0 failed (`lib/utils.test.ts`).

### 6.2. Recommended Test Enhancements
1. **Frontend Component Tests:** Add React Testing Library tests for key components (`PVTCalculator.tsx`, `DeclineCurveAnalysis.tsx`, `WellFileUploadForm.tsx`).
2. **E2E Visual Verification:** Implement Playwright automated test scripts for desktop user flows and snapshot testing.

---

## 7. Performance & Scientific Computing

### 7.1. Workload Processing
* Heavy numerical tasks (IMPES grid updates, Prophet cross-validation, XGBoost grid search) currently run **synchronously** within FastAPI endpoint handlers.
* **Risk:** Long simulation runs can exceed HTTP timeout thresholds or block Uvicorn event loop threads under high concurrent load.
* **Recommendation:** Introduce background task execution (FastAPI `BackgroundTasks` or Celery/Redis task queue) with task status polling endpoints (`/api/v1/jobs/{job_id}`).

### 7.2. Package Footprint
* Large scientific dependencies (`vtk`, `pyvista`, `prophet`, `xgboost`, `segyio`) contribute to package size (~500MB). Virtualenv configuration and CI environment caching are essential for optimal build speeds.

---

## 8. Internationalization (I18N / L10N)

* **Current Status:** The user interface and API response messages contain mixed Portuguese (e.g., "Engenharia de Reservatórios", "Salvar Configuração") and English strings.
* **Strategy Roadmap:** Follow `I18N_L10N_PLAN.md` to introduce `next-intl` or `react-i18next` on the frontend and localized message dictionaries on the backend.

---

## 9. Actionable Recommendations Matrix

| Priority | Category | Finding / Issue | Recommended Action |
| :---: | :---: | :--- | :--- |
| **Critical** | Backend | Shared global state instances (`res_simulator`, `dca_analyzer`, `ai_predictor`, `static_model_analyzer`). | Refactor endpoints to stateless request handlers or introduce user/session-scoped resource managers. |
| **High** | Frontend | Legacy `src/pages` route alongside App Router (`app/`). | Migrate `src/pages/pvt-analysis.jsx` to Next.js App Router under `app/pvt-analysis/page.tsx` and delete `src/pages`. |
| **High** | Security | Moderate severity vulnerability in nested `esbuild` dependency (`GHSA-67mh-4wv8-2f99`). | Add `pnpm.overrides` for `esbuild: "^0.25.0"` in `petrolumen/package.json` and run `pnpm install`. |
| **Medium** | Performance | Heavy scientific computations run synchronously in route handlers. | Offload long-running simulations and AI fitting tasks to background tasks with polling endpoints. |
| **Medium** | Testing | Lightweight frontend test coverage (6 unit tests). | Add component tests for core calculators and Playwright E2E integration tests. |
| **Low** | Cleanup | Residual database files in root directory (`default_app_data.db`, `default_reservoir_data.db`). | Ensure root `.gitignore` excludes `.db` files and relocate default seeds into `backend/`. |

---

## 10. Conclusion

The PetroLúmen repository demonstrates a **solid engineering foundation** with exceptional backend test coverage (177 passing tests), high-fidelity reservoir calculations, modern frontend client architecture, and robust authentication mechanisms.

Addressing the **backend state concurrency model**, resolving the **frontend esbuild dependency advisory**, and **expanding frontend testing** will elevate PetroLúmen to a fully scalable, enterprise-grade reservoir engineering platform.
