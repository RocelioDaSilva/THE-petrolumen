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
