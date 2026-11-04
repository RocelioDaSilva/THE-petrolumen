# Licensing Guide

## Policy

> **PetroLumen itself ships under the licence declared in backend/pyproject.toml. Never import a GPL library into the same Python process; if a GPL engine is needed, invoke it as a subprocess.**

---

## 1. Permissive (Safe to Import Directly)

The following libraries are distributed under permissive open-source licenses and are approved for direct in-process import, linking, and embedding within the PetroLúmen application runtime and backend calculation engines:

- **resqpy** (`Apache-2.0`): RESQML standards parsing, manipulation, and geological model exchange.
- **GeostatsPy** (`MIT`): Geostatistical data analysis, variography, and spatial modeling.
- **PyVista** (`MIT`): 3D VTK-based spatial visualization and mesh representation.
- **pint** (`BSD`): Unit definitions, dimensional analysis, and numerical unit conversions.
- **pydantic** (`MIT`): Runtime data validation and API schema definition.
- **FastAPI** (`MIT`): Asynchronous API web framework and routing.
- **NumPy / SciPy / pandas** (`BSD` / `Apache`): Core scientific, numerical, and tabular data processing.

---

## 2. GPL-3.0 (Subprocess Only)

Components licensed under the GNU General Public License v3.0 (`GPL-3.0`) impose strong copyleft requirements. To preserve PetroLúmen's permissive architecture and prevent derivative-work license contagion:

- **Strict Isolation Rule:** Do **not** import these libraries into the same Python process as PetroLúmen.
- **Execution Mechanism:** All interactions must occur via independent subprocesses, standardized command-line invocations, or decoupled file-based interfaces.

Covered tools:
- **pyResToolbox** (`GPL-3.0`): Reservoir engineering analytical tools and calculators.
- **MRST** (`GPL-3.0`): MATLAB/GNU Octave Reservoir Simulation Toolbox routines.
- **ResInsight** (`GPL-3.0`): 3D post-processing, visualization, and plotting engine.

---

## 3. External Binary (Do Not Link)

- **OPM Flow** (`OSL-3.0` / `GPL` parts): OPM Flow contains modules licensed under the Open Software License 3.0 and GPL components. It must be treated strictly as an external binary executable rather than a linked library. PetroLúmen interacts with OPM Flow by assembling input deck files (e.g., standard `.DATA` format), triggering the solver executable via subprocess in an isolated background job runner, and parsing output vectors/restart files.

---

## 4. LGPL (Review Terms)

- **Petres** (`LGPL`): Reservoir calculations, material balance, and decline analysis. While dynamic linking is generally permissible under LGPL terms, review of distribution terms and isolation requirements is necessary before direct in-process linking. Subprocess or service isolation remains the preferred pattern.

---

## Summary Matrix

| Package | Licence | How to use in PetroLumen | Notes |
| :--- | :--- | :--- | :--- |
| **FastAPI** | MIT | Direct in-process import | Core REST API web framework and dependency injection. |
| **pydantic** | MIT | Direct in-process import | Input validation and response serialization schemas. |
| **NumPy / SciPy / pandas** | BSD / Apache | Direct in-process import | Core array calculations, linear algebra, and tabular data processing. |
| **resqpy** | Apache-2.0 | Direct in-process import | Open-source RESQML standard geological model reader and writer. |
| **GeostatsPy** | MIT | Direct in-process import | Variogram analysis and spatial geostatistics. |
| **PyVista** | MIT | Direct in-process import | 3D mesh and grid visualization rendering. |
| **pint** | BSD | Direct in-process import | Physical unit conversion and dimensional consistency. |
| **pyResToolbox** | GPL-3.0 | Subprocess only | Never import in-process; invoke via isolated CLI wrapper or subprocess. |
| **MRST** | GPL-3.0 | Subprocess only | Run research simulation scripts via Octave/MATLAB subprocess. |
| **ResInsight** | GPL-3.0 | Subprocess only | Trigger 3D post-processing and export snapshots via standalone CLI. |
| **OPM Flow** | OSL-3.0 / GPL parts | External binary (do not link) | Export `.DATA` decks, execute external solver binary, parse output files. |
| **Petres** | LGPL | Review terms | Evaluate LGPL linking constraints; prefer subprocess isolation. |
