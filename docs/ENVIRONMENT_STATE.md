# PetroLúmen Environment & System State

**Last Verified:** October 2024 / November 2024 Audit & Refactoring Cycle
**Environment Status:** Fully Operational (100% Green)
**Platform Runtime:** Node.js v20+ / npm v10+

---

## 1. System Environment Overview

| Component | Technology | Version / Spec | Status |
| :--- | :--- | :--- | :---: |
| **Framework** | React | 18.3.1 | 🟢 Healthy |
| **Language** | TypeScript | 5.7.3 | 🟢 Healthy (0 lint errors) |
| **Build Tool** | Vite | 6.4.5 | 🟢 Healthy (20s production build) |
| **Styling** | Tailwind CSS | 3.4.17 | 🟢 Healthy |
| **Theme System** | Dark / Light Mode | Persisted via `localStorage` | 🟢 Healthy |
| **Code Splitting** | Dynamic `React.lazy()` + Suspense | 25 modules split on-demand | 🟢 Healthy |
| **Error Handling** | Localized `ErrorBoundary` + Dev Stack | Class component with props i18n | 🟢 Healthy |
| **State Registry** | SessionRegistry Context | Strict anti-bleed session guard | 🟢 Healthy |
| **UI Components** | Custom Tailwind + Lucide Icons | Lucide 0.469.0 | 🟢 Healthy |
| **Visualization** | Recharts & HTML5 Canvas | Recharts 2.15.0 | 🟢 Healthy |
| **PDF Reporting** | jsPDF & html2canvas | jsPDF 2.5.2 / html2canvas 1.4.1 | 🟢 Healthy |
| **Golden Benchmarks**| Custom Test Runner via `tsx` | 11 suites / 92 physical tests | 🟢 100% Passed |
| **Unit Test Engine** | Vitest + React Testing Library | 5 suites / 18 unit tests | 🟢 100% Passed |

---

## 2. Core Operational Scripts

The root `package.json` defines the following primary development and operational scripts:

```bash
# 1. Install Project Dependencies
npm install

# 2. Start Development Web Server (Port 3000)
npm run dev

# 3. Execute TypeScript Type Check / Linting (0 errors)
npm run lint

# 4. Compile Production Distribution (tsc + vite build)
npm run build

# 5. Preview Production Build
npm run preview

# 6. Execute Full Test Suite (11 Golden Suites + Vitest Unit Tests)
npm test

# 7. Execute Only Golden Benchmarks (92 tests)
npm run test:benchmarks

# 8. Execute Only Vitest Unit Tests (18 tests)
npm run test:unit

# 9. Create Production Release Package (ZIP)
npm run package
```

---

## 3. Latest Build & Verification Output

* **Type Check (`npm run lint`):** Passed with 0 errors (`tsc --noEmit`).
* **Production Compilation (`npm run build`):**
  - **Modules Transformed:** 2,540
  - **Build Time:** ~20.6s
  - **Output Directory:** `dist/`
  - **Distribution CSS:** `dist/assets/index-ChzSiCsn.css` (44.34 kB)
  - **Core Distribution JS:** `dist/assets/index-CHLSJuLJ.js` (~165.19 kB uncompressed / 51.24 kB gzipped) — down from 1.53 MB thanks to full code-splitting!
  - **Lazy Loaded View Modules:** All 25 view components are now dynamically code-split into distinct chunks with `<LoadingSkeleton />` fallback.
* **Golden Test Suite Results:** 11 / 11 suites passed (92 / 92 physical tests green).
* **Unit Test Suite Results:** 5 / 5 suites passed (18 / 18 unit tests green).
* **Total Automated Tests:** 110 automated tests executing in under 25 seconds with 100% pass rate.
