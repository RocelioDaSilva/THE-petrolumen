# PetroLúmen Developer Onboarding Guide

Welcome to the PetroLúmen project! This guide is designed to help new developers quickly understand the project architecture, set up their local environment, run development tools, and execute the automated scientific benchmark and unit test suites.

---

## 1. Project Overview

PetroLúmen is a web application for Petroleum & Reservoir Engineering built with **React 18**, **TypeScript 5**, **Vite 6**, and **Tailwind CSS**.

The project integrates 25 specialized interactive domain views covering:
* **Drilling & Well Operations:** Well Control, Mud Hydraulics, Drilling Fluids, Cementing, Directional Surveying, Stuck Pipe, Rig Loads, Ton-Miles, Air/Gas Drilling, Core Analysis, and Completions.
* **Surface Facilities:** 2-Phase and 3-Phase Separator Sizing (Arnold & Stewart 2008), Oil & Water Treating, Tank Capacities.
* **Reservoir Engineering & Simulation:** 1D IMPES Pressure Diffusivity Solver, 3D Geocellular Voxel Grid ($8 \times 8 \times 4$), Decline Curve Analysis (Arps & Duong), PVT Thermodynamics & Phase Envelope Editor, Nodal Analysis (Vogel/Darcy + Beggs & Brill), Rate Transient Analysis (FMB), Production Economics, Machine Learning Forecasting, and LAS Log Visualizer.

---

## 2. Essential Project Documentation

* **Root Project README:** [`README.md`](../README.md) - High-level overview, feature catalog, and execution commands.
* **Audit Documentation:**
  * [`docs/audits/CURRENT_STATE_AUDIT.md`](./audits/CURRENT_STATE_AUDIT.md) - Comprehensive deep audit report, scorecard, and performance metrics.
  * [`docs/audits/DEEP_AUDIT_REPORT.md`](./audits/DEEP_AUDIT_REPORT.md) - Technical mathematical analysis.
  * [`docs/ENVIRONMENT_STATE.md`](./ENVIRONMENT_STATE.md) - Current system environment, build output metrics, and test coverage inventory.
* **Agent Guidelines:** [`AGENTS.md`](../AGENTS.md) - Rules and best practices for AI agents working in this repository.

---

## 3. Developer Setup Checklist

Follow these steps to get your local environment running:

1. **Prerequisites:**
   - Node.js version 20 or higher.
   - npm version 10 or higher.

2. **Clone and Install:**
   ```bash
   git clone <repository-url>
   cd petrolumen
   npm install
   ```

3. **Start Development Server:**
   ```bash
   npm run dev
   # Open browser at http://localhost:3000
   ```

4. **Verify Type Safety & Compilation:**
   ```bash
   npm run lint
   # Executes `tsc --noEmit` (enforces 0 errors)
   ```

5. **Build for Production:**
   ```bash
   npm run build
   # Generates optimized distribution artifacts in `dist/`
   ```

6. **Create Distribution Package:**
   ```bash
   npm run package
   # Builds and creates `petrolumen-release.zip`
   ```

---

## 4. Testing Guidelines

PetroLúmen has a dual test infrastructure:
1. **Engineering Golden Benchmarks (92 tests across 11 suites):** Verifies thermodynamic, drilling, and facilities equations against verified literature standards.
2. **Unit Tests via Vitest (18 tests across 5 test suites):** Verifies React components, state contexts, unit conversions, and fail-loudly parameter guards.

Run all tests with a single command:
```bash
npm test
```

Or run test suites independently:
```bash
# Run only engineering golden benchmark suites (92 tests)
npm run test:benchmarks

# Run only Vitest unit tests (18 tests)
npm run test:unit
```

---

## 5. Coding Standards & Best Practices

* **TypeScript Strictness:** Always maintain strict type annotations. Avoid untyped `any` or silent type coercions.
* **Component Architecture:** Reusable primitive components reside in `src/components/ui/`, while domain-specific views are located in `src/components/visualizations/`.
* **Code-Splitting:** All heavy view modules in `src/App.tsx` must be loaded dynamically using `React.lazy()` wrapped with `<Suspense fallback={<LoadingSkeleton />}>`.
* **State Isolation:** Never mutate global or shared state across scenarios. Use `useSessionRegistry()` to read and update parameters inside `<SessionRegistryProvider>`.
* **Fail Loudly on Unphysical Parameters:** As mandated by `AGENTS.md`, thermodynamic and drilling formulas must never return silent zeros or clamp unphysical parameters (e.g. negative pressures or temperatures below absolute zero) without throwing an explicit `RangeError`.
* **Pre-commit Verification:** Always execute `npm run lint` and `npm test` before submitting pull requests.
