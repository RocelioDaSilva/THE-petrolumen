# PetroLúmen Developer Onboarding Guide

Welcome to the PetroLúmen project! This guide is intended to help new developers get up to speed with the project structure, setup, and development workflows.

## 1. Purpose of This Guide

This document provides a quick start for developers joining the PetroLúmen project. It complements the more detailed README files found within specific parts of the repository.

## 2. Essential Project Documentation

Before diving into the code, please familiarize yourself with the following key documents:

*   **Root Project README**: [README.md](../README.md) - Provides a general overview of the PetroLúmen project.
*   **Backend README**: [backend/README.md](../backend/README.md) - Detailed information about the Python FastAPI backend, including setup, running, and testing.
*   **Frontend README**: [petrolumen/README.md](../petrolumen/README.md) - Detailed information about the Next.js/Tauri frontend application, including setup, running, and building.
*   **Agent Instructions**: [AGENTS.md](../AGENTS.md) - Guidelines for AI agents working with this codebase.
*   **Security Policy**: [SECURITY.md](../SECURITY.md) - Important security best practices for development.

## 3. Initial Developer Setup Checklist

Here's a summarized checklist to get your development environment ready:

*   **[ ] Clone the Repository**:
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```
*   **[ ] Backend Setup (Python/FastAPI)**:
    *   Navigate to `backend/`.
    *   Create and activate a Python virtual environment (`python -m venv venv && source venv/bin/activate` or `venv\Scripts\activate`).
    *   Install dependencies: `pip install -r requirements.txt`.
    *   Set up environment variables: Copy `backend/.env.example` to `backend/.env` and configure (especially `SECRET_KEY` and `DATABASE_URL`).
    *   Run database migrations: `alembic upgrade head`.
    *   Refer to `backend/README.md` for more details.
*   **[ ] Frontend Setup (Next.js 15/Tauri v2/pnpm)**:
    *   Navigate to `petrolumen/`.
    *   Install dependencies: `pnpm install`.
    *   Set up environment variables: If `petrolumen/.env.local.example` exists, copy it to `petrolumen/.env.local` and configure.
    *   Refer to `petrolumen/README.md` for more details, including Rust setup for Tauri.
*   **[ ] Verify Setup**:
    *   Run the backend server (from `backend/`): `uvicorn main:app --reload --port 8000`.
    *   Run the frontend development server (from `petrolumen/`): `pnpm tauri dev`.

## 4. Version Control Strategy

*   **Branching**:
    *   Create new branches from `main`.
    *   Use descriptive branch names (e.g., `feature/name-of-feature`, `fix/issue-description`, `docs/update-readme`).
*   **Commits**:
    *   Make small, logical commits.
    *   Write clear and concise commit messages.
*   **Pull Requests (PRs)**:
    *   Push your branch to the remote repository and open a PR against `main`.
    *   Ensure your PR includes a clear description of the changes and links to relevant issues.
    *   Ensure all automated checks and test suites pass.

## 5. Testing Guidelines

Running tests is crucial to maintain code quality.

*   **Backend Tests**:
    *   Navigate to `backend/` (with virtual environment activated).
    *   Run: `pytest`
    *   For coverage: `pytest --cov=gaia_genesis --cov-report=html`
*   **Frontend Tests**:
    *   Navigate to `petrolumen/`.
    *   Unit/Component tests: `pnpm test`
    *   End-to-End tests: `pnpm test:e2e`

Always ensure tests pass before submitting a Pull Request.

## 6. Staying Updated and Contributing

*   **Future Improvements**: For an overview of planned enhancements and areas for contribution, please see [FUTURE_IMPROVEMENTS_JULY.md](./plans/FUTURE_IMPROVEMENTS_JULY.md).
*   **Code Style**: Adhere to existing code style and conventions (PEP 8 for Python, standard TypeScript/React practices for frontend).
*   **Pre-commit Hooks**: Pre-commit hooks (`.pre-commit-config.yaml`) run automatically to ensure linting and formatting.

Happy coding!
