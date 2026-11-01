# Contributing to PetroLúmen

Thank you for contributing. The active web application is the repository-root Vite/React application; the Python package in `backend/` is a separate, smaller set of calculation engines. Historical Tauri/Next.js copies elsewhere in this workspace are not the default development target.

## Prerequisites

- Node.js compatible with the root package dependencies
- npm
- Python 3.11 or newer for backend work

## Frontend setup and checks

Run these commands from the repository root:

```bash
npm install
npm run dev
npm run lint
npm test
npm run build
```

`npm run lint` performs the TypeScript no-emit check. `npm test` runs the engineering benchmark runner and Vitest suite. `npm run build` type-checks and builds the Vite application.

## Backend setup and checks

From the repository root:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
python -m pip install -e "backend[dev]"
python -m pytest backend/tests
```

See [`backend/README.md`](./backend/README.md) and [`backend/pyproject.toml`](./backend/pyproject.toml) for the backend package details.

## Contribution guidelines

- Keep changes focused and include or update tests for behavior changes.
- Preserve engineering units, documented assumptions, and golden benchmark fidelity.
- Engineering calculations should reject unphysical inputs explicitly rather than silently returning plausible-looking values.
- Update the relevant canonical documentation when behavior or setup changes.
- Keep generated outputs, local records, reference libraries, and copied project trees out of commits.
- Use a descriptive branch name and commit message. Open a pull request with a concise summary, validation results, and any relevant limitations.
