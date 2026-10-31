# PetroLúmen Backend

This is the Python backend (FastAPI) for the PetroLúmen petroleum engineering calculation engines.

## Directory Structure

```
backend/
├── app/
│   ├── core/
│   │   ├── units.py            # Unit conversion engine (ported from src/lib/units.ts)
│   │   └── sanitize.py         # PVT input sanitization & validation (ported from src/lib/pvt/sanitize.ts)
│   └── engines/
│       └── drilling/
│           └── well_control.py # Well control calculations & schedules (Wait & Weight, Driller's Method)
├── tests/
│   └── golden/
│       └── test_carter_well_control.py # Carter Ch. 3 golden benchmark test suite
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
pip install fastapi pydantic pytest
```

## Running Golden Tests

Run the golden benchmark test suite from the repository root:

```bash
pytest backend/tests/golden/
```

Or from within the `backend/` directory:

```bash
cd backend
pytest tests/golden/
```
