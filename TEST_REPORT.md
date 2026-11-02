# PetroLúmen Automated Test & Verification Report

**Date of Verification:** November 2026
**Execution Environment:** Linux x86_64, Node.js v22.22.1, Python 3.12.13
**Status:** All 121 Automated Tests Green (100% Pass Rate)

---

## 1. Physical Engineering Benchmark Suites (92/92 Passed - 100%)

The physical calculation engine was validated against published literature benchmarks and textbooks:

1. **Cormack (2017) [7/7 Passed]**
   - Combined pump speed and mud weight laws
   - Multiple annular section influx height calculation (DC-OH + DP-OH)
   - Mandatory Kill Mud Weight round-up rule
   - Conservative Maximum Mud Weight round-down rule
   - Swab pressure trip margin
   - Kill sheet volume roll-up
   - PVT sanitization & thermodynamic boundary validation (fail-loudly)

2. **Bourgoyne et al. (1986) [8/8 Passed]**
   - Hoisting system loads (fast line tension and mast load)
   - Duplex double-acting pump displacement factor and hydraulic horsepower
   - Fann rotational viscometer rheology (PV, YP, Power-Law indices)
   - Barite weight-up ideal mixing equations
   - API Class G cement slurry design (yield and density)
   - Bit jet pressure drop and hydraulic impact force
   - API Barlow casing burst rating with 12.5% mill tolerance
   - Minimum curvature directional survey and Dogleg Severity (DLS)

3. **API Bulletin 5C3 & Teale (1965) [7/7 Passed]**
   - Casing collapse plastic regime (7" 29 lb/ft N-80, 9⅝" 47 lb/ft N-80)
   - Standard grade D/t boundary limits (9⅝" 40 lb/ft J-55)
   - Thick-walled yield collapse regime (Lamé thick-wall equations)
   - Elastic Euler buckling collapse regime
   - Teale (1965) Mechanical Specific Energy (MSE) bit efficiency
   - Triplex single-acting pump displacement factor

4. **Arnold & Stewart (2008) [10/10 Passed]**
   - Gas apparent molecular weight & specific gravity
   - Sour gas Wichert-Aziz correction and compressibility factor
   - Vertical two-phase separator sizing
   - Horizontal two-phase separator sizing (with literature errata correction)
   - Vertical three-phase separator sizing
   - Horizontal three-phase separator sizing
   - FWKO pressure vessel weight estimation (ASME Sec VIII Div 1)
   - Gunbarrel external water leg height hydrostatic balance
   - Horizontal heater-treater sizing & heat duty
   - CPI plate separator droplet cutoff diameter

5. **Carter et al. (2023 - 5th Edition) [60/60 Passed]**
   - Ch. 3 Well Control & Kick Sheets (15/15 tests)
   - Ch. 4 Drilling Fluids & Retort Analysis (12/12 tests)
   - Ch. 5 Cement Slurries & Plug Bumping (3/3 tests)
   - Ch. 6 Drilling Hydraulics & ECD (7/7 tests)
   - Ch. 2 Rig Capacity, Trip Time & Bit Wear (7/7 tests)
   - Ch. 2.6 Stuck Pipe & Fishing Economics (6/6 tests)
   - Phase 7 Formation Pressure & LOT (5/5 tests)
   - Phase 8 Directional Surveying & DLS (5/5 tests)

---

## 2. Frontend Unit & Integration Test Suite (18/18 Passed - 100%)

Executed via Vitest:
- `src/lib/__tests__/pvt.spec.ts` (7 tests): Standing correlations, Hall-Yarborough Z-factor, fail-loudly boundary checks.
- `src/lib/__tests__/sessionRegistry.spec.tsx` (3 tests): Context isolation, session switching, error handling outside provider.
- `src/components/__tests__/ErrorBoundary.spec.tsx` (2 tests): Render crash interception, localized error feedback, retry capability.
- `src/lib/__tests__/lasParser.spec.ts` (2 tests): Standard LAS 2.0 parsing, track mapping, NaN-to-null sanitization.
- `src/lib/__tests__/units.spec.ts` (4 tests): Bi-directional Field <-> SI conversions (pressure, length, rate, volume, density, viscosity).

---

## 3. Backend Python Engine Tests (29/29 Passed - 100%)

Executed via `pytest`:
- `backend/tests/golden/test_carter_well_control.py` (15 tests): Well control equations parity with TypeScript implementation.
- `backend/tests/test_engines.py` (14 tests): Math utilities, ECD, driller simulation, trajectory, ROP physics, Arps decline curve, petrophysics facies, and gas material balance.

---

## 4. Code Quality & Static Typing

- **TypeScript Typecheck:** `npm run lint` (`tsc --noEmit`) - 0 errors.
- **Python Static Linting:** `ruff check backend/` - 0 errors.
- **Python Type Safety:** `mypy --ignore-missing-imports backend/app/` - 0 errors.
- **Production Bundle:** `npm run build` completed successfully.
