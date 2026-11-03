# PetroLúmen Project Documentation

This directory houses project-wide documentation that applies to the PetroLúmen application as a whole or doesn't fit specifically within the `backend/docs_sphinx/` or `petrolumen/docs/` directories.

## Purpose

The `docs/` directory at the root of the project serves as a central repository for:

*   **High-Level Architectural Overviews:** Diagrams and descriptions of the overall system architecture, interactions between frontend and backend, and major data flows.
*   **Contribution Guidelines (Overall Project):** General guidelines for contributing to any part of the PetroLúmen project, supplementing specific guidelines in sub-modules.
*   **Architecture Decision Records (ADRs):** Documents that capture important architectural decisions made throughout the project's lifecycle, including the context, decision, and consequences. (A subdirectory like `docs/adr/` might be created for these).
*   **Cross-Cutting Concerns:** Documentation related to topics that span multiple parts of the application, such as security policies (`SECURITY.md` is at root, but detailed security architecture could be here), overall deployment strategies, or project-wide coding conventions if not covered elsewhere.
*   **Glossary of Terms:** Definitions of domain-specific terms used within the PetroLúmen project.
*   **Meeting Notes & Design Documents:** Important discussions or design specifications that have broader project impact.

## Navigating Documentation

*   For **backend-specific (Python/FastAPI) generated API documentation and technical details**, see `backend/docs_sphinx/` (once generated) and `backend/README.md`.
*   For **frontend-specific (Next.js/Tauri) documentation**, including UI component guidelines, see `petrolumen/docs/` and `petrolumen/README.md`.
*   For **developer onboarding**, see [DEVELOPER_ONBOARDING.md](../DEVELOPER_ONBOARDING.md) in the root directory.
*   For the **list of future improvements and ongoing tasks**, see [FUTURE_IMPROVEMENTS_JULY.md](../FUTURE_IMPROVEMENTS_JULY.md) in the root directory.

This centralized `docs/` directory aims to make it easier to find information that is crucial for understanding and contributing to the PetroLúmen project effectively.
