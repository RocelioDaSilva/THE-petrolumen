# PetroLúmen Backend

This is the Python backend (FastAPI) for the PetroLúmen petroleum engineering calculation engines.

## Directory Structure

```
backend/
├── app/
│   ├── core/
│   │   ├── units.py            # Unit conversion engine (ported from src/lib/units.ts)
│   │   └── sanitize.py         # PVT input sanitization & validation (ported from src/lib/pvt/sanitize.ts)
│   ├── engines/
│   │   ├── drilling/
│   │   │   ├── driller_sim.py  # Driller's method simulation
│   │   │   ├── ecd.py          # Hydrostatic & ECD calculations
│   │   │   ├── trajectory.py   # 3D wellbore trajectory (minimum curvature)
│   │   │   └── well_control.py # Well control calculations & schedules (Wait & Weight, Driller's Method)
│   │   ├── reservoir/
│   │   │   ├── decline_curve.py# Arps decline curve analysis models (exponential, hyperbolic, harmonic)
│   │   │   └── nodal.py        # Nodal analysis (Vogel IPR and TPR)
│   │   ├── petrophysics/
│   │   │   └── porosity.py     # Log porosity and petrophysical evaluations
│   │   └── analytics/
│   │       └── event_detection.py # Time-series rolling anomaly & kick detection
│   └── utils/
│       └── math_utils.py       # Geometric and mathematical utilities (deg2rad, min_curvature)
├── tests/
│   ├── golden/
│   │   └── test_carter_well_control.py # Carter Ch. 3 golden benchmark test suite
│   └── test_engines.py         # Modular calculation engines unit tests
├── pyproject.toml
└── README.md
```

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
pip install fastapi pydantic pytest numpy scipy pandas
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
