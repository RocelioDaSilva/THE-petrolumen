# Agent Instructions

This document provides guidelines and instructions for AI agents working with the PetroLúmen codebase.

## General Guidelines

*   Familiarize yourself with the project structure:
    *   `src/`: Main Application Engine (React 18, TypeScript 5, Vite 6, Tailwind CSS). Contains petroleum engineering calculation modules, components, and UI views.
    *   `src/lib/`: Verified engineering math engines (Drilling, Well Control, PVT, Facilities, Reservoir IMPES, Economics).
    *   `docs/`: Architecture documentation, audits, onboarding guides, and engineering specifications.
*   Refer to [README.md](file:///c:/Users/rocel/THE-petrolumen/README.md) for full application capabilities and scientific reference literature.
*   Ensure any code changes are accompanied by relevant unit tests and preserve benchmark fidelity.
*   Follow standard TypeScript and React best practices.

## General Principles for AI Agents

*   **Clarity and Readability:** Prioritize writing clear, understandable, and maintainable code.
*   **Comments:** Add comments to explain complex physics logic, empirical formulas, assumptions, or non-obvious engineering decisions.
*   **Testing:** Strive to add or update tests for any new features or bug fixes. Run `npm test` before committing.
*   **Incremental Changes:** Prefer smaller, focused commits over large, monolithic ones.
*   **Engineering Rigor:** Always maintain mathematical consistency with petroleum industry standards (Bourgoyne et al., Arnold & Stewart, API 5C3, Cormack 2017).

## Working with the Application (`/`)

*   The frontend is built with React 18, TypeScript 5, Vite 6, and Tailwind CSS.
*   **Package Manager:** Use `npm` for package management in the root repository.
*   **Installation:**
    *   Run `npm install`.
*   **Development Mode:**
    *   Run `npm run dev`. This starts the Vite dev server with hot-reloading at `http://localhost:3000`.
*   **Building for Production:**
    *   Run `npm run build` (`tsc && vite build`).
*   **Typechecking & Linting:**
    *   Run `npm run lint` (`tsc --noEmit`).

## Running Tests

*   **Engineering Math Benchmarks & Unit Tests:**
    *   Run `npm test` (executes `npx tsx src/testRunner.ts`).
    *   To run individual golden test suites:
        *   `npx tsx src/lib/drilling/__tests__/bourgoyneGoldenTests.ts`
        *   `npx tsx src/lib/facilities/__tests__/arnoldStewartGoldenTests.ts`
        *   `npx tsx src/lib/drilling/__tests__/cormackGoldenTests.ts`

## Important Notes

*   All thermodynamic, drilling, and facilities equations must fail loudly on unphysical parameters rather than returning misleading zeros.
*   Unit conversion consistency between Field and SI units must be preserved across all calculation engines and UI components via `unitContext.tsx` and `units.ts`.
