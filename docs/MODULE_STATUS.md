# PetroLúmen Platform Module & Verification Status

**Target Release:** PetroLúmen v1.0.0 (verification target)
**Status:** Provisional — under verification
**Date:** November 11, 2026

---

## 1. Executive Summary

The application currently functions in the tested workflows. The recorded test runs pass (196 backend tests, 92 engineering benchmarks, and 37 frontend Vitest tests); these results do not certify every module or engineering use. The Windows production bundle build has been successfully verified: setting `TEMP` and `TMP` to the project-local `.temp/` directory avoids the esbuild temporary-file cleanup failure and generates `dist/index.html` plus `dist/assets`. The installed desktop workflow's GUI presentation and backend deployment/bindings remain under verification.

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

This matrix is a capability inventory, not evidence that every listed module has been independently tested or certified. See [`TEST_REPORT.md`](../TEST_REPORT.md) for the recorded test and build results.

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
