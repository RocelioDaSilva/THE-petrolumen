# PetroLúmen Backend

This is the Python backend (FastAPI) for the PetroLúmen petroleum engineering calculation engines.

## Directory Structure

```
backend/
├── app/
│   ├── core/
│   │   ├── units.py            # Unit conversion engine (ported from src/lib/units.ts)
│   │   └── sanitize.py         # PVT input sanitization & validation (ported from src/lib/pvt/sanitize.ts)
│   ├── api/
│   │   ├── engine_routes.py    # General calculation endpoints
│   │   └── reservoir_compressibility_routes.py # Compressibility endpoints
│   ├── engines/
│   │   ├── drilling/
│   │   │   ├── driller_sim.py  # Driller's method simulation
│   │   │   ├── ecd.py          # Hydrostatic & ECD calculations
│   │   │   ├── rop.py          # Rate of penetration (ROP) prediction and Carter physics
│   │   │   ├── trajectory.py   # 3D wellbore trajectory (minimum curvature)
│   │   │   └── well_control.py # Well control calculations & schedules (Wait & Weight, Driller's Method)
│   │   ├── reservoir/
│   │   │   ├── decline_curve.py   # Arps decline curve analysis models (exponential, hyperbolic, harmonic)
│   │   │   ├── compressibility.py # Rock, gas, and total compressibility calculations
│   │   │   ├── material_balance.py# Flowing material balance (FMB) P/Z & OGIP estimation
│   │   │   ├── nodal.py           # Nodal analysis (Vogel IPR and TPR)
│   │   │   └── pvt.py             # Thermodynamic PVT correlations (Z-factor, Standing Pb & Bo)
│   │   ├── petrophysics/
│   │   │   ├── facies.py       # Random Forest facies classification & log prediction
│   │   │   └── porosity.py     # Log porosity and petrophysical evaluations
│   │   └── analytics/
│   │       ├── event_detection.py # Time-series rolling anomaly & kick detection
│   │       └── sequences.py       # Time-series sliding window & sequence normalization
│   └── utils/
│       └── math_utils.py       # Geometric and mathematical utilities (deg2rad, min_curvature)
├── tests/
│   ├── golden/
│   │   └── test_carter_well_control.py # Carter Ch. 3 golden benchmark test suite
│   ├── test_reservoir_compressibility.py # Correlation and validation tests
│   ├── test_reservoir_compressibility_routes.py # API contract tests
│   └── test_engines.py         # Modular calculation engines unit tests
├── pyproject.toml
└── README.md
```

## Reservoir engine organization

The actively wired calculation modules live in `app/engines/reservoir/` and
are imported by the API in `app/api/`. Compressibility HTTP schemas and
endpoints are in `app/api/reservoir_compressibility_routes.py`, separate from
the calculation functions. New production-ready calculations should be added
to `app/engines/reservoir/`, exported from that package, and covered by unit
and route tests. The separate `app/reservoir/` tree currently contains
playbook-oriented scaffolding and incomplete modules; it is not the source of
the API calculations documented above. Keep that distinction explicit until
the scaffold is migrated feature-by-feature with regression tests.

The first compressibility workflow is exposed at:

- `POST /api/engine/reservoir/compressibility/rock` — Newman's sandstone and
  limestone pore-volume correlations.
- `POST /api/engine/reservoir/compressibility/gas` — gas isothermal
  compressibility from the project's Hall-Yarborough Z curve and Sutton
  pseudocritical properties. This is not a reproduction of the book's DAK
  worked-example curve; the response identifies the selected Z correlation.
- `POST /api/engine/reservoir/compressibility/total` — phase-weighted fluid
  compressibility plus rock pore-volume compressibility.

All compressibility outputs use `psi^-1`; pressure is in `psia`, temperature
in `degF`, and porosity and saturations are fractions. Rock correlations
outside their published porosity interval are allowed by default but reported
as out-of-range; set `strict` (or `strict_rock_range`) to reject those cases.
These are engineering correlations, not a substitute for core/PVT laboratory
data or a validated reservoir simulator.

The reservoir capability response at `GET /api/v1/reservoir/capabilities`
includes the methods wired to that router and a scoped list of newer
compressibility calculations, along with known limitations and explicit
non-goals. It is not a full API inventory.

## Setup & Installation

Ensure Python 3.11+ is installed.

1. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies (and editable package):

```bash
pip install -e ".[dev]"
```

Alternatively, install the core requirements directly:

```bash
pip install fastapi pydantic pytest numpy scipy pandas scikit-learn
```

## Running Tests

Run the full test suite from the repository root:

```bash
pytest backend/tests/
```

Or from within the `backend/` directory:

```bash
cd backend
pytest
```
