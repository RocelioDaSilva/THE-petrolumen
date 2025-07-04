# API Integration Guide (Frontend <-> Backend)

This document outlines how the frontend (PetroLúmen Next.js app) integrates with the Python FastAPI backend.

## API Contract and Documentation

The backend API is built with FastAPI, which automatically generates an OpenAPI 3.0 specification. This specification serves as the contract between the frontend and backend.

**Accessing API Documentation:**

When the backend server is running (typically at `http://localhost:8000`), the following interactive API documentation interfaces are available:

-   **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
-   **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

These interfaces allow you to:
-   View all available API endpoints, their HTTP methods, parameters (path, query, request body), and response models.
-   Inspect the schemas of Pydantic models used for requests and responses.
-   Interactively try out API endpoints directly from your browser.

The OpenAPI schema itself can usually be accessed at `http://localhost:8000/openapi.json`.

## Frontend API Client (`petrolumen/lib/backendClient.ts`)

Currently, the frontend uses a manual API client located at `petrolumen/lib/backendClient.ts`. This client includes:
-   A base `fetchWithAuth` function that automatically retrieves the JWT token from `localStorage` and adds it to the `Authorization` header for authenticated requests.
-   Specific functions for each API endpoint (e.g., `loginForAccessToken`, `getCurrentUser`, `uploadWellData`, etc.).
-   TypeScript interfaces for request and response payloads (e.g., `UploadResponse`, `UserProfileResponse`).

This client has been updated to include functions for newly integrated features.

## Newly Integrated API Endpoint Groups

As part of recent updates, several new groups of API endpoints, primarily leveraging the `gaia_genesis` toolkit, have been added to the backend. These are fully documented in the auto-generated OpenAPI specification (Swagger/ReDoc) accessible via `/docs` and `/redoc` when the backend is running.

Key new endpoint groups include:

-   **Gaia - PVT Calculations (`/api/v1/gaia/pvt/...`)**:
    -   Endpoints for calculating fluid properties like Z-Factor, Formation Volume Factor, Viscosity, and Solution Gas Ratio.
    -   These were already partially integrated and have been verified.

-   **Gaia - Reservoir Analysis Tools (`/api/v1/gaia/reservoir-tools/...`)**:
    -   Material Balance: Endpoints for OGIP and STOIIP calculations.
    -   Well Testing: Endpoints for analyzing pressure buildup and drawdown tests.
    -   Decline Curve Analysis: Endpoint for EUR (Estimated Ultimate Recovery) calculation from Arps parameters.

-   **Gaia - Static Modeling Tools (`/api/v1/gaia/static-modeling/...`)**:
    -   Endpoints for defining a 3D grid and adding well data for static models.
    -   Variogram calculation and fitting.
    -   Kriging interpolation.
    -   Rock physics calculations (Gassmann, Hertz-Mindlin).
    -   NMR T2 data analysis.
    -   *Note: Some of these endpoints operate on a shared global instance in the backend and may not be concurrency-safe. Grid and well data setup are stateful.*

-   **Reservoir Engineering - AI Prediction (`/api/v1/reservoir/prediction/...`)**:
    -   Endpoints for training AI models (SVR, XGBoost) for general regression tasks.
    -   Predicting with trained models.
    -   Saving and loading trained models.
    -   *Note: The AI predictor instance is global. Training a new model will overwrite the previously trained models in that instance unless models are explicitly saved and loaded.*

-   **Reservoir Engineering - Decline Curve Analysis (`/api/v1/reservoir/dca/...`)**:
    *   Endpoints for fitting Arps decline curves and predicting future rates.
    *   These have been refactored to use a stateless `DeclineAnalysis` class.

-   **Reservoir Engineering - Flow Simulation (`/api/v1/reservoir/flowsim/...`)**:
    *   Endpoints for setting up and running flow simulations.
    *   *Note: These endpoints operate on a shared global simulator instance and are not concurrency-safe. A `/reset` endpoint is provided for single-user workflow management.*

Please refer to the Swagger UI (`/docs`) or ReDoc (`/redoc`) for detailed request/response schemas and to try out these new endpoints.

## Recommended: Client Code Generation

To improve type safety, reduce boilerplate, and ensure better synchronization between the frontend and backend API definitions, it is **highly recommended** to use an OpenAPI client code generator.

**Suggested Tool:** `openapi-typescript-codegen` or `openapi-generator-cli` (with a TypeScript generator like `typescript-fetch` or `typescript-axios`).

**Benefits:**
-   **Type Safety:** Automatically generates TypeScript interfaces from the backend's Pydantic models, catching mismatches early.
-   **Reduced Boilerplate:** Creates typed functions for API calls.
-   **Synchronization:** Simplifies updating the frontend client when the API changes.

**Example Workflow (using `openapi-typescript-codegen`):**

1.  **Install (as a dev dependency):**
    ```bash
    # In petrolumen directory
    pnpm add -D openapi-typescript-codegen
    # or npm install --save-dev openapi-typescript-codegen
    ```

2.  **Add a script to `package.json`:**
    ```json
    "scripts": {
      // ... other scripts
      "generate-api-client": "openapi-typescript http://localhost:8000/openapi.json --output ./lib/apiClientGenerated.ts"
    }
    ```
    *(Adjust output path as needed, e.g., `lib/backendClient/generated.ts`)*

3.  **Run the script:**
    ```bash
    pnpm generate-api-client
    # or npm run generate-api-client
    ```
    *(Ensure the backend server is running when you execute this command so `/openapi.json` is accessible).*

4.  **Use the generated client:** Import types and functions from the generated file into your frontend components or services. This would replace or augment the current manual implementations in `backendClient.ts`.

## API Conventions

-   **Authentication:** JWT Bearer tokens are used for authentication, passed in the `Authorization` header.
-   **Error Responses:** Errors from the API typically follow the FastAPI default structure, often including a `detail` field with the error message. The `ApiErrorResponse` class in `backendClient.ts` attempts to parse this.
-   **Base URL:** The API base URL is configured via `NEXT_PUBLIC_API_BASE_URL` environment variable (see `.env.example` in the frontend and backend configuration).

By adhering to the OpenAPI specification and leveraging code generation, frontend development can be made more efficient and robust when interacting with the backend API.
