# Licensing Guide

This document establishes the licensing classification and integration rules for all third-party libraries, external calculation engines, and binary tools utilized across PetroLúmen.

---

## 1. Permissive (Safe to Import Directly)

The following libraries are distributed under permissive open-source licenses and are approved for direct in-process import, linking, and embedding within the PetroLúmen application runtime and backend engines:

- **resqpy** (`Apache-2.0`): RESQML standards parsing, manipulation, and data exchange.
- **GeostatsPy** (`MIT`): Geostatistical data analysis and variography modeling.
- **PyVista** (`MIT`): 3D VTK-based spatial visualization and mesh representation.
- **pint** (`BSD-3-Clause`): Unit definitions, dimensional analysis, and numerical unit conversions.
- **pydantic** (`MIT`): Runtime data validation and API schema definition.
- **FastAPI** (`MIT`): Asynchronous API web framework and routing.
- **NumPy / SciPy / pandas** (`BSD-3-Clause` / `Apache-2.0`): Core scientific, numerical, and tabular data processing.

---

## 2. GPL-3.0 (Subprocess-Isolated Only)

Components licensed under the GNU General Public License v3.0 (`GPL-3.0`) impose strong copyleft requirements. To preserve PetroLúmen's permissive architecture and prevent derivative-work license contagion:

- **Strict Isolation Rule:** Do **not** import these libraries into the same Python process as PetroLúmen.
- **Execution Mechanism:** All interactions must occur via independent subprocesses, standardized command-line invocations, or decoupled file-based interfaces.

Covered tools:
- **pyResToolbox** (`GPL-3.0`): Reservoir engineering analytical tools and calculators.
- **MRST** (`GPL-3.0`): MATLAB/GNU Octave Reservoir Simulation Toolbox routines.
- **ResInsight** (`GPL-3.0`): 3D post-processing, visualization, and plotting engine.

---

## 3. External Binary Only

- **OPM Flow** (`OSL-3.0` / `GPL` components): OPM Flow contains modules licensed under the Open Software License 3.0 and GPL components. It must be treated strictly as an external binary executable rather than a linked library. PetroLúmen interacts with OPM Flow by assembling input deck files (e.g., standard `.DATA` format), triggering the solver executable via subprocess in an isolated background job runner, and parsing output vectors/restart files.

---

## 4. LGPL

- **Petres** (`LGPL-3.0`): Reservoir calculations, material balance, and decline analysis. While dynamic linking is generally permissible under LGPL terms, code review and legal verification of distribution mechanisms are required before any direct in-process linking. Subprocess or service isolation remains the preferred pattern.

---

## 5. Policy

> **PetroLumen itself ships under the MIT License.**
>
> Never import a GPL library into the same process. If a GPL engine is needed, invoke it via subprocess.
