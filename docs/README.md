# PetroLúmen Project Documentation

Welcome to the central documentation index for the **PetroLúmen Petroleum & Reservoir Engineering Platform**.

---

## 📚 Navigation & Directory Map

* **Onboarding & Setup:**
  - [Developer Onboarding Guide (`docs/DEVELOPER_ONBOARDING.md`)](./DEVELOPER_ONBOARDING.md) - Local setup, execution commands, and developer checklist.
  - [Environment & System State (`docs/ENVIRONMENT_STATE.md`)](./ENVIRONMENT_STATE.md) - System specifications, dependency inventory, build metrics, and operational scripts.

* **Audits & Quality Assurance:**
  - [Current State Audit Report (`docs/audits/CURRENT_STATE_AUDIT.md`)](./audits/CURRENT_STATE_AUDIT.md) - Latest comprehensive audit findings, scorecard, test results, vulnerability findings, and bundle metrics.
  - [Deep Repository Audit (`docs/audits/DEEP_AUDIT_REPORT.md`)](./audits/DEEP_AUDIT_REPORT.md) - Deep dive into mathematical engines, golden benchmarks, and code structure.
  - [Dependency Audit (`docs/audits/DEPENDENCY_AUDIT_REPORT.md`)](./audits/DEPENDENCY_AUDIT_REPORT.md) - Historical dependency analysis.

* **Architecture & Future Roadmaps:**
  - [Session Registry Design (`docs/design/SESSION_REGISTRY.md`)](./design/SESSION_REGISTRY.md) - Architectural design for session management.
  - [Future Enhancements (`docs/plans/FUTURE_IMPROVEMENTS_JULY.md`)](./plans/FUTURE_IMPROVEMENTS_JULY.md) - Long-term feature backlog and improvement roadmap.
  - [Internationalization Plan (`docs/plans/I18N_L10N_PLAN.md`)](./plans/I18N_L10N_PLAN.md) - Multilingual support plan.

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
