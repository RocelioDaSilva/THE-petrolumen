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
    *   `SECRET_KEY`: A secret key used for security purposes, particularly for JWT token generation. **Change this to a strong, unique random string for production.**
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

(Instructions for running tests will be added here once the test suite is finalized. Typically, it would involve `pytest`.)

```bash
# Example: pytest tests/
```
