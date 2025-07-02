# PetroLúmen - Engenharia de Reservatórios

Welcome to the PetroLúmen project! This document provides a high-level overview of the project structure and how to get started.

## Project Overview

PetroLúmen is a comprehensive application designed for reservoir engineering. It combines a modern desktop frontend with a powerful backend to deliver a suite of tools for data analysis, simulation, and prediction in the oil and gas industry.

## Project Structure

This project is organized into the following main components:

*   **Frontend (`petrolumen/`):** A desktop application built with React/Next.js and packaged natively using Tauri. It provides the user interface for interacting with the reservoir engineering tools. For detailed information about the frontend, its features, and how to run it, please refer to the [frontend README](./petrolumen/README.md).
*   **Backend (Assumed `../backend/` or a separate repository):** The backend is expected to be a Python application (potentially using FastAPI or a similar framework) that handles data processing, simulations, and API services. *Note: The exact location and setup instructions for the backend should be confirmed and documented here.*

## Getting Started

To get the full application running, you will typically need to set up both the frontend and the backend.

1.  **Frontend Setup:**
    *   Navigate to the `petrolumen` directory.
    *   Follow the instructions in the [frontend README](./petrolumen/README.md) for installation and running the application.

2.  **Backend Setup:**
    *   *(Placeholder: Specific instructions for setting up and running the backend need to be added here. This might involve navigating to the backend directory, installing Python dependencies, and starting a server.)*
    *   If the backend has its own `README.md`, link to it here.

## Key Features

PetroLúmen offers a range of functionalities, including:

*   Data upload and validation
*   Decline curve analysis (Exponential, Hyperbolic, Harmonic)
*   AI-based prediction models (XGBoost, SVR)
*   Interactive data visualization
*   Automated report generation
*   Reservoir simulation capabilities
*   Database integration for data management

(For a more detailed list of features, especially concerning the frontend application, please see the [frontend README](./petrolumen/README.md).)

## Contributing

*(Placeholder: Add guidelines for contributing to the project, such as coding standards, pull request process, etc.)*

## License

*(Placeholder: Specify the license under which this project is distributed, e.g., MIT, Apache 2.0. If there's a `LICENSE` file, link to it.)*

---

*This README provides a general guide to the PetroLúmen project. For more specific details on the frontend application, please consult the `petrolumen/README.md` file.*
