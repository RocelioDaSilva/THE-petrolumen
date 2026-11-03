# PetroLúmen Backend

This directory contains the Python FastAPI backend for the PetroLúmen application. It provides the API services for data management, reservoir engineering calculations, simulations, and more.

## Setup and Running

Follow these steps to set up and run the backend server. It's recommended to use Python 3.9 or newer.

### 1. Create and Activate a Virtual Environment

It's highly recommended to use a virtual environment to manage project dependencies.

Navigate to this `backend` directory and run:
```bash
python -m venv venv
```

Activate the virtual environment:

*   On macOS and Linux:
    ```bash
    source venv/bin/activate
    ```
*   On Windows:
    ```bash
    .\venv\Scripts\activate
    ```
You should see `(venv)` at the beginning of your command prompt.

### 2. Install Dependencies

With the virtual environment activated, install the required Python packages:
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

The application uses environment variables for configuration, such as database connection strings and secret keys.

1.  Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
2.  Open the `.env` file in a text editor and modify the variables as needed:
    *   `DATABASE_URL`: Specifies the connection string for the database. By default, it's set up for a local SQLite database (`sqlite:///./default_app_data.db`). You can change this to use PostgreSQL or another supported database.
        *   Example for PostgreSQL: `postgresql://user:password@host:port/database_name`
    *   `SECRET_KEY`: A secret key used for security purposes, particularly for JWT token generation.

        > **SECURITY WARNING:** The default `SECRET_KEY` in `.env.example` and `config.py` is a placeholder and **MUST NOT** be used in a production environment. Using the default key poses a significant security risk, as it could allow attackers to forge authentication tokens or gain unauthorized access.
        >
        > **Action Required:** Generate a strong, unique random string for your `SECRET_KEY`. You can generate one using tools like OpenSSL:
        > ```bash
        > openssl rand -hex 32
        > ```
        > Copy the generated string into your `.env` file for the `SECRET_KEY` variable.

    *   Other variables related to logging, API versions, etc., can also be configured here.

### 4. Set Up the Database (Alembic Migrations)

This project uses Alembic to manage database schema migrations. After configuring your `DATABASE_URL` in the `.env` file, apply the migrations to set up your database tables:

```bash
alembic upgrade head
```
This command will create the necessary tables based on the latest migration scripts. If you are starting with an empty database, this will set up the initial schema.

### 5. Run the Development Server

Once the setup is complete, you can run the FastAPI development server using Uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

*   `--reload`: Enables auto-reloading when code changes are detected.
*   `--host 0.0.0.0`: Makes the server accessible from your local network (not just `localhost`).
*   `--port 8000`: Specifies the port to run on.

The backend API will then be available at `http://localhost:8000`.
You can access the automatically generated API documentation (Swagger UI) at `http://localhost:8000/docs` and ReDoc at `http://localhost:8000/redoc`.

## Project Structure Overview

*   `main.py`: The main FastAPI application entry point.
*   `config.py`: Handles application configuration using Pydantic settings.
*   `database.py`: Contains database session management logic.
*   `alembic/`: Directory for Alembic database migration scripts.
*   `alembic.ini`: Configuration file for Alembic.
*   `gaia_genesis/`: The core application logic, including:
    *   `api_v1/`: FastAPI routers and endpoints for version 1 of the API.
    *   `core/`: Core components like database models (`database_models.py`), authentication (`auth_manager.py`), data uploading (`data_uploader.py`), and database interactions (`database_manager.py`).
    *   Modules for specific reservoir engineering functionalities (e.g., `production_analysis.py`, `reservoir_simulation.py`, `prediction/ai_prediction.py`).
*   `tests/`: Contains automated tests for the backend (currently under development/review).
*   `requirements.txt`: Lists the Python dependencies for the project.

## Running Tests

Automated tests are written using `pytest`. To run the tests:

```bash
# Ensure your virtual environment is activated and test dependencies are installed.
# From the `backend/` directory:
pytest
# Or, from the project root:
# pytest backend/tests/
```
You can also generate a coverage report if `pytest-cov` is installed:
`pytest --cov=gaia_genesis --cov-report=html` (from `backend/` directory)

## API Versioning

The PetroLúmen backend API employs a path-based versioning strategy. Current stable API endpoints are located under the `/api/v1/` path prefix.

### Current Version: v1
All endpoints for the first stable version of the API are grouped under `/api/v1/`. For example, `http://localhost:8000/api/v1/users` or `http://localhost:8000/api/v1/wells`.

### Introducing Future API Versions (e.g., v2)
When introducing breaking changes to the API, a new version should be introduced by incrementing the version number in the URL path. For example, a new version (v2) would have its endpoints under `/api/v2/`.

**Key Principles for New Versions:**

1.  **Clear Path:** New versions must use a distinct path prefix (e.g., `/api/v2/`, `/api/v3/`).
2.  **Coexistence:** Older versions of the API (e.g., `/api/v1/`) should be maintained for a reasonable period alongside newer versions to allow clients to migrate gradually.
3.  **Breaking Changes:** Only introduce new API versions for changes that are not backward-compatible. For backward-compatible changes (e.g., adding new optional fields to a response, adding new endpoints), these can typically be incorporated into the existing latest stable API version.
4.  **Documentation:** Each API version must be clearly documented (e.g., via Swagger/OpenAPI docs specific to that version, or clearly delineated sections).
5.  **Deprecation Strategy:**
    *   When a new API version (e.g., v2) supersedes an older one (e.g., v1), a clear deprecation timeline for the old version should be communicated to API consumers.
    *   This includes announcing the deprecation, setting a sunset date (when the old version will be turned off), and providing migration guides.
    *   Consider using a custom `X-API-Version-Deprecated` header or similar in responses from deprecated API versions to warn clients.
6.  **Code Organization:** In the backend codebase, new API versions should ideally be organized in separate modules or packages (e.g., `gaia_genesis/api_v2/`) to maintain clarity and separation from older versions.

This approach ensures that clients can rely on a stable API version while allowing for future evolution and improvements.

## Building Documentation (Sphinx)

The backend documentation is built using Sphinx. The Sphinx configuration is located in `backend/docs_sphinx/`.

**Prerequisites:**
*   Ensure you have activated your Python virtual environment for the backend (`source venv/bin/activate` or `venv\Scripts\activate`).
*   All dependencies from `requirements.txt` must be installed (`pip install -r requirements.txt`), which includes Sphinx and the theme.

**To build the HTML documentation:**
1.  Navigate to the Sphinx documentation directory:
    ```bash
    cd docs_sphinx
    ```
2.  Run the make command to build the HTML version:
    ```bash
    make html
    ```
3.  The generated HTML documentation will be available in `backend/docs_sphinx/_build/html/`. You can open `index.html` in that directory in a web browser to view the docs.

The build output directory (`_build/`) is ignored by Git.
