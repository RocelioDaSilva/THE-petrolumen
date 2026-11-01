# PetroLúmen Project Documentation

Welcome to the central documentation index for the **PetroLúmen Petroleum & Reservoir Engineering Platform**.

## Source of truth and document status

**Active product:** the repository-root Vite/React application (`src/`, root `package.json`) and the Python calculation package in `backend/`.

The root `README.md`, `CONTRIBUTING.md`, `AGENTS.md`, `backend/README.md`, and this index are the primary contributor-facing documents. Nested Tauri/Next.js project trees are experiments or historical copies, not the default product.

Use the following status labels when adding or refreshing documentation:

| Status | Meaning |
|---|---|
| Current | Verified against the active product and current commands. |
| Proposed | A design or plan that has not been confirmed as implemented. |
| Historical | A dated record of an earlier implementation or audit. |
| Archived | Retained for reference, but not maintained as current guidance. |

Audits and environment reports must state their verification date, source commit, and commands/evidence. Older reports below are historical unless explicitly revalidated.

---

## 📚 Navigation & Directory Map

* **Onboarding & Setup:**
  - [Developer Onboarding Guide (`docs/DEVELOPER_ONBOARDING.md`)](./DEVELOPER_ONBOARDING.md) - Local setup, execution commands, and developer checklist.
  - [Environment & System State (`docs/ENVIRONMENT_STATE.md`)](./ENVIRONMENT_STATE.md) - System specifications, dependency inventory, build metrics, and operational scripts.

* **Audits & Quality Assurance:**
  - [Current State Audit Report (`docs/audits/CURRENT_STATE_AUDIT.md`)](./audits/CURRENT_STATE_AUDIT.md) - Snapshot; verify its date, test counts, and metrics before relying on it as current.
  - [Deep Repository Audit (`docs/audits/DEEP_AUDIT_REPORT.md`)](./audits/DEEP_AUDIT_REPORT.md) - Historical technical audit.
  - [Dependency Audit (`docs/audits/DEPENDENCY_AUDIT_REPORT.md`)](./audits/DEPENDENCY_AUDIT_REPORT.md) - Historical dependency snapshot, not current vulnerability status.
  - [Historical reports](./archive/README.md) - Archived audits and document copies, when present.

* **Architecture & Future Roadmaps:**
  - [Session Registry Design (`docs/design/SESSION_REGISTRY.md`)](./design/SESSION_REGISTRY.md) - Proposed design; confirm implementation status.
  - [Future Enhancements (`docs/plans/FUTURE_IMPROVEMENTS_JULY.md`)](./plans/FUTURE_IMPROVEMENTS_JULY.md) - Historical brainstorm; migrate active items to tracked issues.
  - [Internationalization Plan (`docs/plans/I18N_L10N_PLAN.md`)](./plans/I18N_L10N_PLAN.md) - Proposed plan; confirm current architecture fit.

---

## 🛠 Quick Terminal Commands

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Check TypeScript types
npm run lint

# Compile production build
npm run build

# Run all golden test suites
for f in src/lib/drilling/__tests__/*.ts src/lib/facilities/__tests__/*.ts; do npx tsx "$f"; done
```
