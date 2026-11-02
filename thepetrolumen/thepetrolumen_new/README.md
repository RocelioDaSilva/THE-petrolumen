# PetroLúmen - Engenharia de Reservatórios

Welcome to the PetroLúmen project! This document provides a high-level overview of the project structure and how to get started.

## Project Overview

PetroLúmen is a comprehensive application designed for reservoir engineering. It combines a modern desktop frontend with a powerful backend to deliver a suite of tools for data analysis, simulation, and prediction in the oil and gas industry.

## Project Structure

This project is organized into the following main components:

*   **Frontend (`petrolumen/`):** A desktop application built with React/Next.js and packaged natively using Tauri. It provides the user interface for interacting with the reservoir engineering tools. For detailed information about the frontend, its features, and how to run it, please refer to the [frontend README](./petrolumen/README.md).
*   **Backend (`backend/`):** A Python application using FastAPI that handles data processing, simulations, and API services. It includes functionalities from the integrated `gaia_genesis` library.

## Getting Started

To get the full application running, you will typically need to set up both the frontend and the backend.

1.  **Frontend Setup:**
    *   Navigate to the `petrolumen` directory.
    *   Follow the instructions in the [frontend README](./petrolumen/README.md) for installation and running the application.

2.  **Backend Setup:**
    *   The backend is located in the `backend/` directory.
    *   Ensure you have Python installed (typically 3.9+).
    *   Create a virtual environment: `python -m venv venv` and activate it (e.g., `source venv/bin/activate` on Linux/macOS, `venv\\Scripts\\activate` on Windows).
    *   Install dependencies: `pip install -r backend/requirements.txt`.
    *   Set up necessary environment variables (e.g., by creating a `.env` file in the `backend/` directory based on `.env.example`). This includes `DATABASE_URL` and `SECRET_KEY`.
    *   Initialize the database: If using Alembic for migrations, run `alembic upgrade head` from within the `backend/` directory.
    *   Run the backend server: `uvicorn main:app --reload --host 0.0.0.0 --port 8000` from within the `backend/` directory.
    *   The backend API documentation (Swagger UI) will be available at `http://localhost:8000/docs`.

## Key Features

PetroLúmen offers a range of functionalities, including:

*   User authentication (JWT-based).
*   Well data upload, storage (via PostgreSQL or SQLite), and retrieval.
*   Basic PVT (Pressure-Volume-Temperature) calculations via API:
    *   Z-Factor
    *   Formation Volume Factor (Oil & Gas)
    *   Viscosity (Oil & Gas)
    *   Solution Gas-Oil Ratio
    *   (Refer to the API documentation at `/docs` on the running backend for details on these endpoints under the "Gaia - PVT Calculations" tag).
*   Decline curve analysis (Exponential, Hyperbolic, Harmonic) via API.
*   Reservoir simulation capabilities (partially integrated, ongoing).
*   AI-based prediction models (placeholder, integration ongoing).
*   Interactive data visualization (primarily via frontend).
*   Database integration for data management using SQLAlchemy and Alembic migrations.

(For a more detailed list of features, especially concerning the frontend application, please see the [frontend README](./petrolumen/README.md).)

## Contributing

We welcome contributions to PetroLúmen! Please follow these general guidelines:
1.  **Fork the repository** and create a new branch for your feature or bug fix.
2.  **Follow existing coding styles.** For Python, we aim for PEP 8 compliance. For TypeScript/React, follow common community best practices.
3.  **Write tests** for new features and bug fixes.
4.  **Ensure all tests pass** before submitting a pull request.
5.  **Keep pull requests focused** on a single feature or bug fix.
6.  **Provide clear commit messages** and a descriptive pull request title and body.
(Further details on specific linters, code formatting tools, and detailed PR procedures can be added here as the project matures.)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
(A `LICENSE` file containing the standard MIT License text should be added to the root of the repository.)

---

*This README provides a general guide to the PetroLúmen project. For more specific details on the frontend application, please consult the `petrolumen/README.md` file.*
