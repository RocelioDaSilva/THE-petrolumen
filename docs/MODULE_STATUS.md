# PetroLúmen Platform Module & Verification Status

**Target Release:** PetroLúmen v1.0.0 (verification target)
**Status:** Provisional — under verification
**Date:** November 12, 2026

---

## 1. Executive Summary

The application currently functions in the tested workflows. The latest recorded verification passes 225 backend tests, 92 engineering benchmarks, and 34 frontend Vitest tests; these results do not certify every module or engineering use. The Windows production bundle build has been successfully verified: setting `TEMP` and `TMP` to the project-local `.temp/` directory avoids the esbuild temporary-file cleanup failure and generates `dist/index.html` plus `dist/assets`.

The PyWebView desktop launcher now serves the built React frontend from `dist/` through its embedded FastAPI server and supplies the dynamically assigned API port to the frontend. The installer includes the built React assets. The React UI uses a dark-first navy/teal design system, with a user-selectable light theme. The launcher smoke test verified that the UI document, JavaScript/CSS assets, and API health endpoint are served successfully. Visual review of the redesigned window is separate from these automated checks.

Recorded verification:

| Check | Result |
| :--- | :--- |
| Backend tests (`python -m pytest backend/tests -q`) | 225 passed, 7 skipped |
| Frontend Vitest tests | 34 passed |
| Engineering benchmark runner | 92/92 passed |
| Production build (`npm run build`) | Passed; emits a warning for large vendor chunks |

---

## 2. Multi-Discipline Module Verification Matrix

| Module Domain | Literature / Governing Physics | Primary Components & Engines | Verification Status | Bilingual (PT/EN) | Method Panel / Worked Solutions |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Reservoir Physics & PVT** | Standing, Hall-Yarborough, Lee-Gonzalez-Eakin, Papay | `src/lib/reservoirMath.ts`, `PVTCalculator.tsx` | Under verification; no standalone certification | Present; coverage not audited | Present; behavior under verification |
| **Well Testing & RTA** | Theis Drawdown, Cooper-Jacob, Horner ($k, s, p^*, p_{1\text{hr}}$), Bourdet $L=0.1$ | `src/lib/reservoirMath.ts`, `FlowingMaterialBalanceView.tsx` | Under verification; no standalone certification | Present; coverage not audited | Present; behavior under verification |
| **Material Balance & Simulation** | Havlena-Odeh, P/Z Straight-Line, 1D Two-Phase IMPES, CFL limit | `ReservoirSimulationView.tsx`, `flow_simulation.py` | Under verification; no standalone certification | Present; coverage not audited | Present; behavior under verification |
| **Drilling Hydraulics & Casing** | Bourgoyne et al. (1986), API Bulletin 5C3, Teale (1965) MSE | `DrillingHydraulicsView.tsx`, `casingDesign.ts`, `bitsAndPower.ts` | Under verification; no standalone certification | Present; coverage not audited | Present; behavior under verification |
| **Well Control & Tripping** | Carter et al. (5th Ed., 2023), Cormack (2017) | `WellControlView.tsx`, `carterWellControlGoldenTests.ts` | Under verification; no standalone certification | Present; coverage not audited | Present; behavior under verification |
| **Surface Facilities & Vessels** | Arnold & Stewart (2008) 2-Phase/3-Phase Separators, FWKO | `SurfaceFacilitiesView.tsx`, `twoPhaseSeparation.ts` | Under verification; no standalone certification | Present; coverage not audited | Present; behavior under verification |
| **Production Nodal & DCA** | Vogel IPR, Fetkovich, Beggs-Brill VLP, Arps, Duong Unconventional | `NodalAnalysisView.tsx`, `DeclineCurveAnalysis.tsx` | Under verification; no standalone certification | Present; coverage not audited | Present; behavior under verification |
| **Fiscal Economics & Sensitivity** | DCF, NPV, IRR, Payback, ROI, PSC Sharing, Automated Tornado | `EconomicsView.tsx`, `src/lib/reservoirMath.ts` | Under verification; no standalone certification | Present; coverage not audited | Present; behavior under verification |
| **Petrophysics & LAS** | Archie ($S_w$), Larionov ($V_{sh}$), Porosity, Net Pay cutoffs | `lasParser.ts`, `WellDataViewer.tsx` | Under verification; no standalone certification | Present; coverage not audited | Present; behavior under verification |

This matrix is a capability inventory, not evidence that every listed module has been independently tested or certified. See [`TEST_REPORT.md`](../TEST_REPORT.md) for broader test and build context.

---

## 3. Core Architecture & Infrastructure

1. **Bi-Directional Quantity & Unit Registry:**
   - Supported Field units: `psia`, `ft`, `bbl/day`, `lb/gal`, `°F`, `mD`, `cP`, `in`.
   - Supported Metric/SI units: `kPa`, `MPa`, `bar`, `m`, `m³/day`, `kg/m³`, `°C`, `mPa·s`, `mm`, `m²`.
   - Synchronized across TypeScript (`src/lib/units.ts`) and Python (`backend/app/core/units.py`).

2. **Bilingual Localization:**
   - Localization infrastructure is present in `src/lib/i18n.tsx`; translation coverage and runtime behavior have not been exhaustively verified.

3. **Session & Versioned Snapshot Registry:**
   - State isolation via `SessionRegistryContext` protecting scenarios from cross-contamination.

4. **Academic Transparency:**
   - Governing equations, literature citations, variable definitions, and boundary condition warnings integrated on core calculation workflows.

5. **Desktop UI:**
   - PyWebView opens the built React application served from the embedded FastAPI process; the separate legacy static desktop page is not the canonical UI.
   - Build the frontend before installing or launching from a source checkout so the `dist/` assets are present.
