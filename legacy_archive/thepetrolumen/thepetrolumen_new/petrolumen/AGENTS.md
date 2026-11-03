# Agent Guidance for PetroLúmen Frontend Development

## Component Structure

When developing new UI components or features, please adhere to the following structure to maintain consistency:

*   **Reusable UI Components:**
    *   Place general-purpose, reusable UI components (e.g., buttons, cards, generic modals) that are not tied to specific features or routes into `components/ui/`.
    *   These components should be designed to be broadly applicable across the application.

*   **Feature-Specific or Route-Specific Components:**
    *   Components that are specific to a particular page, route, or feature within the Next.js App Router (`app/`) should be co-located with their respective routes. For example, components used only by `app/dashboard/page.tsx` could reside in `app/dashboard/components/`.
    *   If a component is used by multiple sub-routes under a particular path segment (e.g. `app/settings/*`), it can be placed in a `components` folder under that segment (e.g. `app/settings/components/`).

*   **Legacy `src/` directory:**
    *   The `src/` directory contains older structures. For new development, prefer the `app/` directory structure for route-based organization and `components/ui/` for globally reusable UI elements. Avoid adding new components to `src/` unless specifically maintaining existing functionality within that structure.

*   **`components/` (root level):**
    *   The top-level `components/` directory (alongside `app/` and `pages/`) should primarily house the `ui/` subdirectory for globally reusable components as mentioned above.
    *   If there are other shared components that don't fit the "UI primitive" category but are used across many unrelated parts of the `app/` directory, they can reside here. However, try to co-locate components with their primary features in `app/` first.

**Goal:** Strive for clarity and make it easy to find components. Co-locate components with the features/routes they serve, and place truly global, reusable UI elements in `components/ui/`.

This guidance aims to clarify the usage of `app/components/`, `components/`, and the legacy `src/` directory.
