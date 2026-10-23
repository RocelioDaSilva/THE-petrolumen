# Agent Instructions

This document provides guidelines and instructions for AI agents working with the PetroLúmen codebase.

## General Guidelines

*   Familiarize yourself with the project structure:
    *   `petrolumen/`: Frontend (Next.js 15, React 19, Tauri v2, TypeScript)
    *   `backend/`: Backend (Python 3.12, FastAPI, SQLAlchemy 2)
*   Refer to the `README.md` files in the root, `petrolumen/`, and `backend/` directories for specific setup and architectural details.
*   Ensure any code changes are accompanied by relevant tests.
*   Follow standard coding conventions for the respective languages (TypeScript for frontend, Python for backend).

## General Principles for AI Agents

*   **Clarity and Readability:** Prioritize writing clear, understandable, and maintainable code.
*   **Comments:** Add comments to explain complex logic, assumptions, or non-obvious decisions.
*   **Testing:** Strive to add or update tests for any new features or bug fixes.
*   **Incremental Changes:** Prefer smaller, incremental commits over large, monolithic ones.
*   **Consult `AGENTS.md` in Subdirectories:** Be aware that subdirectories (e.g., `petrolumen/`, `backend/`) may contain their own `AGENTS.md` files with more specific instructions. Always check for and adhere to the guidance in the most specific `AGENTS.md` file applicable to the files you are modifying.
*   **Future Improvements:** Refer to `docs/plans/FUTURE_IMPROVEMENTS_JULY.md` for a broader list of potential enhancements to the repository.

## Working with the Frontend (`petrolumen/`)

*   The frontend is built with Next.js 15 / React 19 and packaged natively using Tauri v2.
*   **Package Manager:** Always use `pnpm` for package management in `petrolumen/`.
*   **Installation:**
    *   Navigate to the `petrolumen/` directory.
    *   Run `pnpm install`.
*   **Development Mode:**
    *   Run `pnpm tauri dev` (or `pnpm dev` for web-only) from the `petrolumen/` directory. This starts the application with hot-reloading.
    *   The frontend connects to the backend API at `http://localhost:8000`.
*   **Building for Production:**
    *   Run `pnpm build` from the `petrolumen/` directory to build the Next.js application.
*   **Packaging Desktop Application:**
    *   Run `pnpm tauri build` from the `petrolumen/` directory.
    *   The installer will be located in `petrolumen/src-tauri/target/release/bundle/`.

## Working with the Backend (`backend/`)

*   The backend is a Python application using FastAPI and SQLAlchemy 2.
*   **Setup:**
    1.  Navigate to the `backend/` directory.
    2.  Create a virtual environment: `python -m venv venv`.
    3.  Activate the virtual environment:
        *   Linux/macOS: `source venv/bin/activate`
        *   Windows: `venv\\Scripts\\activate`
    4.  Install dependencies: `pip install -r requirements.txt`.
    5.  Configure environment variables: Copy `backend/.env.example` to `backend/.env` and update as needed (`DATABASE_URL`, `SECRET_KEY`).
    6.  Set up the database: Run `alembic upgrade head` from the `backend/` directory to apply database migrations.
*   **Running the Development Server:**
    *   From the `backend/` directory (with venv activated): `uvicorn main:app --reload --host 0.0.0.0 --port 8000`.
*   **API Documentation:**
    *   Swagger UI: `http://localhost:8000/docs`
    *   ReDoc: `http://localhost:8000/redoc`
*   **Core Logic:** Main application domain logic is in `backend/gaia_genesis/`.

## Code Conventions

*   **Python (Backend):** Follow PEP 8 guidelines.
*   **TypeScript/React (Frontend):** Adhere to common community best practices.
*   **General:** When contributing, fork the repository, create a new branch, write tests for your changes, ensure all tests pass, keep pull requests focused, and use clear commit messages.

## Running Tests

*   **Frontend (`petrolumen/`):**
    *   Unit/Component tests: `pnpm test` (executes `vitest run`).
    *   End-to-End tests: `pnpm test:e2e` (executes Playwright test suite).
*   **Backend (`backend/`):**
    *   From the `backend/` directory (with venv activated): `pytest`.
    *   To generate coverage: `pytest --cov=gaia_genesis --cov-report=html`.

## Important Notes

*   The backend uses Alembic for database schema migrations. Ensure migrations are run after any database model changes or when setting up the environment.
*   The backend's core functionalities are organized within the `gaia_genesis` Python package.
*   For detailed setup and architectural information, refer to `README.md` files in root, `petrolumen/`, and `backend/`.
