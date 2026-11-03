# PetroLúmen Developer Onboarding Guide

Welcome to the PetroLúmen project! This guide is intended to help new developers get up to speed with the project structure, setup, and development workflows.

## 1. Purpose of This Guide

This document provides a quick start for developers joining the PetroLúmen project. It complements the more detailed README files found within specific parts of the repository.

## 2. Essential Project Documentation

Before diving into the code, please familiarize yourself with the following key documents:

*   **Root Project README**: [README.md](./README.md) - Provides a general overview of the PetroLúmen project.
*   **Backend README**: [backend/README.md](./backend/README.md) - Detailed information about the Python FastAPI backend, including setup, running, and testing.
*   **Frontend README**: [petrolumen/README.md](./petrolumen/README.md) - Detailed information about the Next.js/Tauri frontend application, including setup, running, and building.
*   **Agent Instructions**: [AGENTS.md](./AGENTS.md) - Guidelines for AI agents working with this codebase (and check for AGENTS.md in subdirectories).
*   **Security Policy**: [SECURITY.md](./SECURITY.md) - Important security best practices for development.

## 3. Initial Developer Setup Checklist

Here's a summarized checklist to get your development environment ready:

*   **[ ] Clone the Repository**:
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```
*   **[ ] Backend Setup (Python/FastAPI)**:
    *   Navigate to `backend/`.
    *   Create and activate a Python virtual environment (e.g., `python -m venv venv && source venv/bin/activate` or `venv\Scripts\activate`).
    *   Install dependencies: `pip install -r requirements.txt`.
    *   Set up environment variables: Copy `backend/.env.example` to `backend/.env` and configure (especially `SECRET_KEY` and `DATABASE_URL`).
    *   Run database migrations: `alembic upgrade head`.
    *   Refer to `backend/README.md` for more details.
*   **[ ] Frontend Setup (Next.js/Tauri/pnpm)**:
    *   Navigate to `petrolumen/`.
    *   Install dependencies: `pnpm install`. (Ensure pnpm is installed: `npm install -g pnpm`).
    *   Set up environment variables: If `petrolumen/.env.local.example` exists, copy it to `petrolumen/.env.local` and configure.
    *   Refer to `petrolumen/README.md` for more details, including Rust setup for Tauri if you intend to build the desktop application.
*   **[ ] Verify Setup**:
    *   Run the backend server (from `backend/`): `uvicorn main:app --reload --port 8000`.
    *   Run the frontend development server (from `petrolumen/`): `pnpm tauri dev`.

## 4. Version Control Strategy

*   **Branching**:
    *   Create new branches from the `main` branch (or the primary development branch).
    *   Use descriptive branch names, e.g., `feature/name-of-feature`, `fix/issue-description`, `docs/update-readme`.
*   **Commits**:
    *   Make small, logical commits.
    *   Write clear and concise commit messages (e.g., imperative mood: "Add user login feature" not "Added user login feature").
*   **Pull Requests (PRs)**:
    *   Push your branch to the remote repository.
    *   Open a Pull Request against the `main` branch.
    *   Ensure your PR includes a clear description of the changes.
    *   Link to any relevant issues.
    *   Ensure all automated checks/tests pass.
    *   Request reviews from appropriate team members or code owners (see `.github/CODEOWNERS`).

## 5. Testing Guidelines

Running tests is crucial to maintain code quality.

*   **Backend Tests**:
    *   Navigate to `backend/` (with virtual environment activated).
    *   Run: `pytest`
    *   For coverage: `pytest --cov=gaia_genesis --cov-report=html`
*   **Frontend Tests**:
    *   Navigate to `petrolumen/`.
    *   Run: `pnpm test` (or `npm run test` / `yarn test` depending on the project's primary script runner, but pnpm is used here).

Always ensure tests pass before submitting a Pull Request. Write new tests for new features or bug fixes.

## 6. Staying Updated and Contributing

*   **Future Improvements**: For an overview of planned enhancements and areas for contribution, please see [FUTURE_IMPROVEMENTS_JULY.md](./FUTURE_IMPROVEMENTS_JULY.md).
*   **Code Style**: Adhere to existing code style and conventions (PEP 8 for Python, common TypeScript/React practices for frontend). Linters (Flake8 for backend, ESLint for frontend) are set up to help enforce this.
*   **Pre-commit Hooks**: This project uses pre-commit hooks (see `.pre-commit-config.yaml`) to automate linting and formatting. Ensure they are installed (`pre-commit install`) and run before committing.

Happy coding! If you have questions, don't hesitate to ask other team members.
