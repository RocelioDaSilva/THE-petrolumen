# PetroLúmen Developer Onboarding Guide

Welcome to the PetroLúmen project! This guide is designed to help new developers quickly understand the project architecture, set up their local environment, run development tools, and execute the automated scientific benchmark test suites.

---

## 1. Project Overview

PetroLúmen is a web application for Petroleum & Reservoir Engineering built with **React 18**, **TypeScript 5**, **Vite 6**, and **Tailwind CSS**.

The project integrates 22 specialized interactive domain views covering:
* **Drilling & Well Operations:** Well Control, Mud Hydraulics, Drilling Fluids, Cementing, Directional Surveying, Stuck Pipe, Rig Loads, Ton-Miles, Air/Gas Drilling, Core Analysis, and Completions.
* **Surface Facilities:** 2-Phase and 3-Phase Separator Sizing (Arnold & Stewart 2008), Oil & Water Treating, Tank Capacities.
* **Reservoir Engineering & Simulation:** 1D IMPES Pressure Diffusivity Solver, 3D Geocellular Voxel Grid ($8 \times 8 \times 4$), Decline Curve Analysis (Arps & Duong), PVT Thermodynamics & Phase Envelope Editor, Nodal Analysis (Vogel/Darcy + Beggs & Brill), Rate Transient Analysis (FMB), Production Economics, Machine Learning Forecasting, and LAS Log Visualizer.

---

## 2. Essential Project Documentation

* **Root Project README:** [`README.md`](../README.md) - High-level overview, feature catalog, and execution commands.
* **Audit Documentation:**
  * [`docs/audits/CURRENT_STATE_AUDIT.md`](./audits/CURRENT_STATE_AUDIT.md) - Comprehensive deep audit report, scorecard, and vulnerability findings.
  * [`docs/audits/DEEP_AUDIT_REPORT.md`](./audits/DEEP_AUDIT_REPORT.md) - Technical mathematical analysis.
  * [`docs/ENVIRONMENT_STATE.md`](./ENVIRONMENT_STATE.md) - Current system environment, build output metrics, and dependency inventory.
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
   # Executes `tsc --noEmit`
   ```

5. **Build for Production:**
   ```bash
   npm run build
   # Generates distribution build artifacts in `dist/`
   ```

---

## 4. Testing Guidelines

The engineering calculation engines in `src/lib/` are continuously verified against canonical benchmark standards using golden test suites.

Run all golden benchmark test suites via `npx tsx`:

```bash
# Drilling & Well Engineering Benchmark Suites
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

# Surface Facilities Sizing Benchmark Suite
npx tsx src/lib/facilities/__tests__/arnoldStewartGoldenTests.ts
```

---

## 5. Coding Standards & Best Practices

* **TypeScript Strictness:** Always maintain strict type annotations. Avoid `any` types.
* **Component Architecture:** Reusable primitive components reside in `src/components/ui/`, while domain-specific views are located in `src/components/visualizations/`.
* **Mathematical Engines:** Core formulas reside in `src/lib/drilling/`, `src/lib/facilities/`, and `src/lib/field/`. All calculations must include unit handling (`src/lib/units.ts`) and input sanitization (`src/lib/pvt/sanitize.ts`).
* **Pre-commit Verification:** Always execute `npm run lint`, `npm run build`, and golden test suites before submitting pull requests.
