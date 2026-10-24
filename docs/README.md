# PetroLúmen Project Documentation

This directory houses project-wide documentation that applies to the PetroLúmen application as a whole or doesn't fit specifically within the `backend/docs_sphinx/` or `petrolumen/docs/` directories.

## Purpose

The `docs/` directory at the root of the project serves as a central repository for:

*   **High-Level Architectural Overviews:** Diagrams and descriptions of the overall system architecture, interactions between frontend and backend, and major data flows.
*   **Audit Reports (`docs/audits/`):** Backend, dependency, concurrency, and repository audit reports.
*   **Development Plans & Roadmaps (`docs/plans/`):** Feature plans, internationalization strategies, and improvement backlogs.
*   **Contribution Guidelines (Overall Project):** General guidelines for contributing to any part of the PetroLúmen project, supplementing specific guidelines in sub-modules.
*   **Architecture Decision Records (ADRs):** Documents that capture important architectural decisions made throughout the project's lifecycle.
*   **Cross-Cutting Concerns:** Documentation related to security policies, deployment strategies, and project-wide conventions.

## Navigating Documentation

*   For **backend-specific (Python/FastAPI) generated API documentation and technical details**, see `backend/docs_sphinx/` and `backend/README.md`.
*   For **frontend-specific (Next.js/Tauri) documentation**, including UI component guidelines, see `petrolumen/docs/` and `petrolumen/README.md`.
*   For **developer onboarding**, see [DEVELOPER_ONBOARDING.md](./DEVELOPER_ONBOARDING.md).
*   For **audit reports**, see [docs/audits/](./audits/).
*   For **future plans and roadmaps**, see [docs/plans/](./plans/).

This centralized `docs/` directory aims to make it easier to find information that is crucial for understanding and contributing to the PetroLúmen project effectively.
