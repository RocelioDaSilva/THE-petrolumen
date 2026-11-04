> **Status: NORTH-STAR VISION — NOT CURRENT PLAN**
> This document describes a 12-month horizon for the reservoir module.
> Current implementation state (Nov 2026) is at the Wave 3/4 stage: 10 endpoints exposed, ~66 tests passing, no persistence layer, black-oil simulator is a toy documented as such.
> Do NOT treat this document as a roadmap for the next 3 months.
> Current roadmap: docs/ROADMAP.md (to be created in a later wave).

# Architecture Vision: Reservoir Module (12-Month Horizon)

## 1. Scope and Design Principles

The primary mission of PetroLúmen's reservoir module is to deliver accessible, production-grade reservoir simulation and modeling workflows without relying on proprietary, vendor-locked software licenses. Grounded in the philosophy of "free at runtime, transparent internals, open standards first, modular boundaries, reproducibility, validate before you trust", the platform treats scientific rigor and codebase inspectability as foundational tenets rather than secondary features.

Every simulation run, petrophysical correlation, and grid operation is designed to run on free or open-source infrastructure with clear algorithmic provenance. Standard data formats (such as RESQML and standard ECLIPSE decks) are embraced as first-class citizens across all data ingestion and export interfaces. Modular architectural boundaries isolate domain logic from external solvers and execution environments, guaranteeing that calculations remain perfectly reproducible across heterogeneous client machines and that every result can be independently validated before operational reliance.

## 2. Architecture Layers

The reservoir system is architected across six distinct, decoupled layers:

- **Presentation:** High-performance web and desktop interfaces (Next.js / Tauri / PyWebView) delivering interactive well management, cross-sectional grid viewers, production dashboarding, and 3D visualization.
- **API:** RESTful FastAPI gateway exposing typed Pydantic endpoints for parameter definition, simulation lifecycle management, operational telemetry, and reporting.
- **Domain:** Pure Python core calculation engines governing material balance, PVT thermodynamics, well performance, petrophysical evaluations, and analytical decline curves.
- **Job Orchestrator:** Asynchronous task queue and background execution manager handling resource-intensive runs, telemetry streaming, batch sensitivity sweeps, and cancellation signals.
- **External Engines:** Isolated execution environments hosting standalone numerical solvers, external simulation binaries, and command-line visualization pipelines.
- **Storage:** Relational persistence (PostgreSQL / SQLite via SQLAlchemy and Alembic migrations) paired with structured binary artifact and grid object storage for run outputs.

## 3. The Free Tool Stack

The following open-source and free-tier tools form the target reservoir calculation, visualization, and orchestration ecosystem:

| Tool | Ecosystem / Role | Primary License | Architectural Role / Usage |
| :--- | :--- | :--- | :--- |
| **OPM Flow** | Reservoir Simulation | OSL-3.0 / GPL-3.0 | High-performance open-source reservoir simulation engine executed as a standalone binary. |
| **JutulDarcy** | Reservoir Simulation | MIT | Advanced Julia-based framework for multiphase porous media flow and differentiable simulation. |
| **MRST** | Simulation / Prototyping | GPL-3.0 | MATLAB/Octave Reservoir Simulation Toolbox used for rapid research prototyping via subprocess. |
| **resqpy** | Standards / I/O | Apache-2.0 | Pure-Python RESQML standard data model library for geological model and grid exchange. |
| **Petres** | Reservoir Engineering | LGPL-3.0 | Specialized reservoir calculations, material balance, and decline analysis. |
| **GeostatsPy** | Geostatistics | MIT | Spatial data analysis, variography, and geostatistical estimation/simulation routines. |
| **pyResToolbox** | Reservoir Engineering | GPL-3.0 | Comprehensive reservoir engineering utilities and analytical tools (subprocess-isolated). |
| **PetroCalc** | Petroleum Calculations | MIT | Fundamental petroleum engineering unit conversions, fluid properties, and hydraulics formulas. |
| **welltest-pta** | Pressure Transient Analysis | MIT | Analytical and semi-analytical pressure derivative calculation and well test interpretation. |
| **PyVista** | 3D Visualization | MIT | Streamlined VTK interface for in-memory and client-side rendering of unstructured 3D reservoir grids. |
| **ResInsight** | 3D Post-Processing | GPL-3.0 | Dedicated 3D visualization tool for reservoir models and well trajectories (standalone process). |
| **SALib** | Uncertainty & Sensitivity | MIT | Sensitivity analysis library supporting Sobol, Morris, and FAST variance-based methods. |
| **pint** | Units of Measure | BSD-3-Clause | Robust, type-safe unit definition, conversion, and dimensional analysis across all calculations. |
| **pydantic** | Validation & Schemas | MIT | Runtime data validation, strict physical constraint enforcement, and API schema generation. |
| **FastAPI** | Backend Framework | MIT | High-concurrency asynchronous REST API framework serving backend engines and job orchestration. |
| **PostgreSQL** | Relational Database | PostgreSQL (MIT-style) | Primary persistent data store for projects, well records, run metadata, and structured outputs. |

## 4. Licensing Implications

Strict adherence to software licenses governs the integration of third-party tools within the PetroLúmen codebase:

- **GPL Subprocess Isolation:** Any component licensed under GPL-3.0 (e.g., `pyResToolbox`, `MRST`, `ResInsight`) must never be imported directly into the PetroLúmen Python process. Interaction is strictly constrained to external subprocess calls, file-based exchange, or decoupled IPC to avoid derivative-work license contagion.
- **External Binaries:** Complex simulators such as `OPM Flow` (licensed under OSL-3.0 / GPL parts) are treated strictly as external executable binaries invoked via the job orchestrator, writing to standard output decks and reading binary summary files.
- **Permissive Imports:** Permissively licensed libraries (Apache-2.0, MIT, BSD) such as `resqpy`, `GeostatsPy`, `PyVista`, `pint`, `pydantic`, and `FastAPI` are safe to import directly into the core application runtime.

## 5. Data Model Entities

The platform organizes reservoir studies around eleven core domain entities:

- **Project:** Top-level administrative and organizational boundary aggregating geological assets, wells, and engineering scenarios.
- **FluidModel:** Thermodynamic fluid property specifications defining black-oil tables, equation-of-state parameters, and PVT correlations.
- **RockModel:** Petrophysical definitions including rock compressibility, porosity-permeability relationships, and saturation function tables (relative permeability and capillary pressure).
- **Grid:** Spatial reservoir discretization representing structured corner-point geometries or unstructured meshes.
- **Well:** Spatial trajectory, completion intervals, perforation history, and mechanical hardware configuration for an individual borehole.
- **Schedule:** Chronological operational constraints, historical production/injection targets, workovers, and bottomhole pressure controls.
- **Case:** Cohesive simulation scenario binding a specific Grid, RockModel, FluidModel, Well set, and operational Schedule.
- **Run:** Individual execution lifecycle instance of a Case tracking execution environment, parameter overrides, start/finish timestamps, and compute logs.
- **ResultSet:** Ingested output tensors, time-series vectors (rates, pressures, cumulative volumes), and dynamic spatial saturation/pressure distributions.
- **Test:** Pressure transient analysis records, well test observations, and historical gauge datasets utilized for parameter tuning.
- **Uncertainty:** Parameter distribution definitions, variogram ranges, and Latin hypercube sampling matrices configured for probabilistic forecasting.

## 6. Validation Programme

Numerical accuracy and engineering validity are benchmarked against standardized, non-negotiable industry suites:

- **SPE1:** Three-dimensional gas injection study evaluating basic gas-oil displacement and solution gas drive dynamics.
- **SPE9:** Highly heterogeneous black-oil comparative problem featuring waterflooding, 26 production wells, and severe permeability contrasts.
- **SPE10:** Ultra-fine geostatistical benchmark (Model 2) testing solver scalability, fine-scale channeling, and transport resolution across millions of cells.
- **Norne:** Full-scale field benchmark providing real-world production history, 4D seismic integration, complex faulting, and structural stratigraphy.

Continuous integration gates enforce automated parity checks against verified reference datasets for these benchmark models before any simulation engine changes are merged.

## 7. Phased Roadmap (M0 → M6)

The 12-month horizon unfolds across seven milestone phases:

- **M0:** Establish foundational data schemas, unit management (pint), and subprocess wrapper architecture for external binaries.
- **M1:** Deliver RESQML grid ingestion via resqpy alongside interactive 3D visualization using PyVista.
- **M2:** Integrate OPM Flow binary execution runner with automated deck generation and summary vector extraction.
- **M3:** Implement PVT laboratory matching, fluid modeling, and black-oil validation against SPE1.
- **M4:** Incorporate analytical pressure transient analysis (welltest-pta) and history matching workflows validated against SPE9.
- **M5:** Support full-field simulation scaling, water/gas coning analysis, and benchmark convergence testing against SPE10.
- **M6:** Enable multi-realization probabilistic forecasting, automated sensitivity sweeps (SALib), and full Norne field history match validation.

## 8. Risks and Mitigations

The primary risks inherent to this architecture and their corresponding mitigations include:

- **External Binary Dependency and Cross-Platform Portability:** Numerical engines like OPM Flow can be challenging to package and maintain across varied operating systems (Windows, macOS, Linux). *Mitigation:* Deliver standardized containerized runners (Docker / Apptainer) and self-contained precompiled binaries with transparent automated installation scripts and fallback cloud execution.
- **Solver Performance and Memory Bottlenecks:** Simulating fine grids (e.g., SPE10) demands substantial RAM and multi-threaded computation that can degrade host performance. *Mitigation:* Decouple execution via an asynchronous job orchestrator with rigorous memory limits, distributed execution options, and adaptive grid coarsening.
- **License Contamination and Compliance Drift:** Inadvertent direct imports of copyleft or GPL libraries could compromise the permissive licensing of the host repository. *Mitigation:* Implement automated static code analysis in CI workflows that flags prohibited imports and enforces subprocess isolation for all GPL-licensed tools.
- **Numerical Discrepancies and Algorithmic Drift:** Minor formulation differences across open-source solvers may yield divergent production forecasts. *Mitigation:* Embed automated golden regression tests against SPE benchmark standards with strict numerical tolerance thresholds.
