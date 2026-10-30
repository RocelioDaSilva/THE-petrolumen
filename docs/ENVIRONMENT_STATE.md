# PetroLúmen Environment & System State

**Last Verified:** Current Audit Cycle
**Environment Status:** Fully Operational
**Platform Runtime:** Node.js v20+ / npm v10+

---

## 1. System Environment Overview

| Component | Technology | Version / Spec | Status |
| :--- | :--- | :--- | :---: |
| **Framework** | React | 18.3.1 | 🟢 Healthy |
| **Language** | TypeScript | 5.7.3 | 🟢 Healthy |
| **Build Tool** | Vite | 6.0.7 | 🟢 Healthy |
| **Styling** | Tailwind CSS | 3.4.17 | 🟢 Healthy |
| **UI Components** | Custom Tailwind + Lucide Icons | Lucide 0.469.0 | 🟢 Healthy |
| **Visualization** | Recharts & HTML5 Canvas | Recharts 2.15.0 | 🟢 Healthy |
| **PDF Reporting** | jsPDF & html2canvas | jsPDF 2.5.2 / html2canvas 1.4.1 | 🟢 Healthy |
| **Test Runner** | tsx | 4.23.15 | 🟢 Healthy |

---

## 2. Core Operational Scripts

The root `package.json` defines the following primary development and operational scripts:

```bash
# 1. Install Project Dependencies
npm install

# 2. Start Development Web Server (Port 3000)
npm run dev

# 3. Execute TypeScript Type Check / Linting
npm run lint

# 4. Compile Production Distribution (tsc + vite build)
npm run build

# 5. Preview Production Build
npm run preview

# 6. Execute Scientific Golden Benchmark Test Suites
npx tsx src/lib/drilling/__tests__/bourgoyneGoldenTests.ts
npx tsx src/lib/drilling/__tests__/carterCementsGoldenTests.ts
npx tsx src/lib/drilling/__tests__/carterFluidsGoldenTests.ts
npx tsx src/lib/drilling/__tests__/carterHydraulicsGoldenTests.ts
npx tsx src/lib/drilling/__tests__/carterPhase7GoldenTests.ts
npx tsx src/lib/drilling/__tests__/carterPhase8GoldenTests.ts
npx tsx src/lib/drilling/__tests__/carterRigOpsGoldenTests.ts
npx tsx src/lib/drilling/__tests__/carterStuckPipeGoldenTests.ts
npx tsx src/lib/drilling/__tests__/carterWellControlGoldenTests.ts
npx tsx src/lib/drilling/__tests__/cormackGoldenTests.ts
npx tsx src/lib/facilities/__tests__/arnoldStewartGoldenTests.ts
```

---

## 3. Latest Build & Verification Output

* **Type Check (`npm run lint`):** Passed with 0 errors (`tsc --noEmit`).
* **Production Compilation (`npm run build`):**
  - **Modules Transformed:** 2,509
  - **Build Time:** ~13.28s
  - **Output Directory:** `dist/`
  - **Distribution CSS:** `dist/assets/index-BhGKDfIn.css` (40.08 kB)
  - **Distribution JS:** `dist/assets/index-DvZ2LHC2.js` (1.53 MB uncompressed / 425.86 kB gzipped)
  - **Lazy Loaded View Modules:** 8 views dynamically split into sub-chunks (`FieldBasicView`, `RigOperationsView`, `StuckPipeView`, `RigLoadsView`, `TonMilesView`, `TankCapacityView`, `AirGasView`, `CompletionsView`).
* **Golden Test Suite Results:** 11 / 11 suites passed with exit code 0.

---

## 4. Dependencies & Security Audit Summary

* Total Installed Packages: 196
* Audited Packages: 197
* Audit Status: 2 vulnerabilities flagged (1 High, 1 Critical) in `dompurify` transitively imported via `jspdf`.
* Resolution Path: Add `overrides` to `package.json` or upgrade `jspdf`.
