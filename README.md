# PetroLúmen - Enterprise Petroleum & Reservoir Engineering Suite

[![Production Build](https://img.shields.io/badge/Build-Passing-brightgreen.svg)]()
[![Engineering Benchmarks](https://img.shields.io/badge/Benchmarks-92%2F92%20Passed-brightgreen.svg)]()
[![Type Safety](https://img.shields.io/badge/TypeScript-Strict-blue.svg)]()
[![License](https://img.shields.io/badge/License-MIT-blue.svg)]()

PetroLúmen is an enterprise-grade, multi-discipline petroleum engineering web application combining Drilling, Surface Facilities, PVT Thermodynamics, Reservoir Flow Simulation, Geocellular 3D Modeling, Well Testing, Production Nodal Analysis, and Fiscal Economics.

---

## 🚀 Key Features & Capabilities

- **Reservoir Engineering:**
  - 1D Two-Phase IMPES numerical flow simulator with Corey relative permeability curves and CFL stability checking.
  - Comprehensive PVT thermodynamics: Standing bubble point, solution GOR, Beggs-Robinson dead oil viscosity, Hall-Yarborough Z-factor, and Lee-Gonzalez-Eakin gas viscosity.
  - Rate Transient Analysis (RTA) & Flowing Material Balance (FMB) straight-line gas forecasting.
  - Havlena-Odeh material balance and Horner build-up well test analysis.

- **Drilling & Well Control:**
  - Full adherence to **Bourgoyne et al. (1986)**, **Carter et al. (5th Ed., 2023)**, and **Cormack (2017)**.
  - Interactive Kill Sheets (Driller's Method & Wait and Weight), MASP, MASICP, and Kick Tolerance Intensity.
  - Bingham Plastic and Power-Law annular hydraulics, Equivalent Circulating Density (ECD), and Teale (1965) Mechanical Specific Energy (MSE).
  - API Bulletin 5C3 casing collapse and burst pressure verification.

- **Surface Facilities:**
  - **Arnold & Stewart (2008)** 2-phase and 3-phase horizontal/vertical vessel sizing.
  - Free Water Knockout (FWKO), horizontal heater-treaters, and CPI plate separator droplet cutoff calculations.

- **Production Engineering & Fiscal Economics:**
  - Nodal Analysis: Vogel and Fetkovich Inflow Performance Relationship (IPR) coupled with Beggs-Brill Vertical Lift Performance (VLP).
  - Decline Curve Analysis (DCA): Arps (exponential, hyperbolic, harmonic) and Duong unconventional models.
  - Discounted cash flow modeling (NPV, IRR, Payback, ROI) with Production Sharing Contract (PSC) terms and automated Tornado sensitivity analysis.

- **Academic Transparency & Bilingual Interface:**
  - Collapsible **Method Panels** detailing governing differential equations, literature citations, and physical assumptions.
  - Step-by-step **Worked-Solution** breakdowns with one-click high-resolution PDF and CSV export.
  - 100% Bilingual localization supporting Portuguese (`pt`) and English (`en`) across all calculation modules, charts, and tables.

---

## 🛠️ Getting Started

### Prerequisites
- Node.js (v20+ recommended)
- Python 3.11+ (for backend engine verification)

### Installation & Execution

```bash
# Install frontend dependencies
npm install

# Start the local development server (or npm start)
npm run start

# Run automated tests and physical benchmarks
npm test

# Build for production
npm run build
```

For backend Python development:
```bash
pip install -e "backend[dev]"
python -m pytest backend/tests/
ruff check backend/
python -m mypy --ignore-missing-imports backend/app/
```

---

## 📚 Documentation & Verification

- [Module Status & Compliance](docs/MODULE_STATUS.md)
- [Automated Test Report](TEST_REPORT.md)
- [Deep Audit Report](docs/audits/DEEP_AUDIT_REPORT.md)
- [Developer Onboarding](docs/DEVELOPER_ONBOARDING.md)
