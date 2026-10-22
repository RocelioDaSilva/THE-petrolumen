# Contributing to PetroLúmen

Thank you for your interest in contributing to PetroLúmen! This document outlines the setup process and guidelines for submitting contributions.

---

## Development Setup

### Backend Setup (Python)

1. **Python Version**: Ensure Python 3.12+ is installed.
2. **Virtual Environment**: Create and activate a virtual environment in the repository root or `backend/` directory:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. **Dependencies**: Install the required Python packages:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. **Running Quality Checks & Tests**:
   ```bash
   cd backend
   ruff check .
   black --check .
   pytest -q
   ```

### Frontend Setup (Next.js / Node.js)

1. **Node & Package Manager**: Ensure Node 20+ and `pnpm` 9+ are installed.
   - Use `pnpm` exclusively for managing frontend dependencies and scripts. Do NOT use `npm` or `yarn`.
2. **Install Dependencies**:
   ```bash
   cd petrolumen
   pnpm install
   ```
3. **Running Quality Checks & Tests**:
   ```bash
   cd petrolumen
   pnpm lint
   pnpm typecheck
   pnpm test -- --run
   pnpm build
   pnpm audit --audit-level=high
   ```

---

## Pull Request Guidelines

- **Branch Naming**: Use descriptive branch names (e.g., `feature/...`, `fix/...`, or `jules/...`).
- **CI Requirement**: **All PRs must pass all CI workflow checks** (`backend`, `frontend`, and `audit` jobs) before being merged.
- **Scope**: Keep changes targeted and do not modify application source code unless required by the task scope.
- **Dependency Management**: Ensure lockfiles (`pnpm-lock.yaml`) are updated whenever package configurations are modified.
