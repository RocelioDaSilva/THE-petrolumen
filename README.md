# PetroLúmen - Engenharia de Reservatórios

Welcome to **PetroLúmen**, a comprehensive reservoir engineering platform combining a modern desktop frontend with a high-performance Python backend for data analysis, numerical simulation, and predictive modeling in the oil and gas industry.

## Tech Stack

- **Frontend:** Next.js 15 / React 19 / Tauri v2 / TypeScript (located in `petrolumen/`)
- **Backend:** Python 3.12 / FastAPI / SQLAlchemy 2 (located in `backend/`)

## Project Structure

This repository is organized into the following main components:

- **Frontend (`petrolumen/`):** Desktop application built with Next.js 15, React 19, and packaged natively using Tauri v2. Uses `pnpm` as the required package manager. For detailed frontend instructions, refer to the [frontend README](./petrolumen/README.md).
- **Backend (`backend/`):** Python application powered by FastAPI and SQLAlchemy 2 that handles data processing, 1D IMPES numerical reservoir simulations, PVT calculations, DCA/RTA analysis, and RESTful API endpoints via the `gaia_genesis` core domain library.
- **Documentation (`docs/`):** Centralized documentation hub containing audit reports ([`docs/audits/`](./docs/audits/)), development plans and roadmaps ([`docs/plans/`](./docs/plans/)), and onboarding guides ([`docs/DEVELOPER_ONBOARDING.md`](./docs/DEVELOPER_ONBOARDING.md)).

## Getting Started

### Prerequisites

- **Node.js** (v18+) & **pnpm** (`corepack enable` or `npm install -g pnpm`)
- **Python** (3.12+)
- **Rust** (required for Tauri native desktop builds)

### 1. Frontend Setup

```bash
cd petrolumen
pnpm install
pnpm dev
```

#### Frontend Testing & Quality Verification:
- **Unit & Component Tests:** `pnpm test`
- **End-to-End (E2E) Tests:** `pnpm test:e2e` (executes Playwright test suite)
- **Linting & Type Checking:** `pnpm lint` and `pnpm typecheck`

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The interactive API documentation (Swagger UI) will be accessible at `http://localhost:8000/docs`.

## Key Features

- **Authentication & Security:** Bearer JWT header-based authentication, role-based access control (RBAC), and bcrypt password hashing.
- **Data Management:** Well log and production data upload, database storage (SQLite / PostgreSQL via SQLAlchemy 2), and retrieval.
- **PVT Calculations:** Black-oil correlations (Standing, Glaso, Vasquez-Beggs) and Peng-Robinson EOS flash solver.
- **Decline Curve Analysis (DCA):** Advanced DCA fitting models (Arps Exponential/Hyperbolic/Harmonic, Duong, PLE, SEPD) using `scipy.optimize`.
- **Reservoir Simulation:** 1D two-phase (oil-water) and dry gas IMPES numerical flow simulator utilizing the Thomas algorithm.
- **Rate Transient & Nodal Analysis:** Flowing Material Balance (FMB) and numerical IPR/TPR inflow solver (`fsolve`).
- **AI & ML Forecasting:** Time-series forecasting with Meta Prophet, SVR, and XGBoost models.
- **Unit Management:** Global unit conversion system supporting Field (US Customary) and Metric (SI) units via Zustand store.

## Known Limitations

- **Synchronous Workloads:** Heavy computational tasks (such as 1D IMPES numerical simulation grid updates and model training) currently run synchronously within FastAPI request handlers, though asynchronous background execution (`BackgroundTasks` with `/api/v1/jobs/{job_id}` status polling) is being adopted across endpoints.
- **Mocked E2E Tests:** Frontend Playwright End-to-End (E2E) integration tests currently mock the backend REST API endpoints rather than requiring a live running backend server.

## Documentation

- **Audit Reports:** Located in [`docs/audits/`](./docs/audits/) (includes backend, dependency, and repository audits).
- **Development Plans & Roadmaps:** Located in [`docs/plans/`](./docs/plans/) (includes future improvements and i18n/l10n strategy).
- **Developer Onboarding:** See [`docs/DEVELOPER_ONBOARDING.md`](./docs/DEVELOPER_ONBOARDING.md).
- **Frontend Architecture:** See [`petrolumen/README.md`](./petrolumen/README.md).
- **Backend Architecture:** See [`backend/README.md`](./backend/README.md).

## Contributing

Please refer to [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines, code formatting standards, and PR procedures.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
