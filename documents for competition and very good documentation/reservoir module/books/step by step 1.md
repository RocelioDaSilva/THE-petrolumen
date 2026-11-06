# PetroLumen Reservoir Module: Complete Step-by-Step Build Document

**Version 1.0 — Practical Build Guide**  
**Scope:** Reservoir module only. Free and open-source toolchain with optional AI acceleration.  
**Prerequisite:** Python 3.11+, basic familiarity with Linux/macOS terminal, Git, and reservoir engineering fundamentals.

---

## How to Use This Document

This is a **build sequence**, not a reference manual. Each phase produces a working artifact that you can test, validate, and then extend. Do not skip validation gates — they are what separate a demo from a tool an engineer can trust.

The document is organized into 12 phases. Phases 0–4 produce a **classical reservoir engineering workbench**. Phases 5–9 add the **AI and agentic layer**. Phases 10–11 add **energy-transition physics and production hardening**. Phase 12 is continuous.

**Estimated total effort for a solo developer working part-time:** 9–15 months for Phases 0–9, with Phases 10–11 extending to 18–24 months. Phases 0–4 alone are achievable in 3–5 months.

---

## Phase 0: Environment and Repository Setup

### 0.1 Operating system

Use **Ubuntu 22.04 LTS or 24.04 LTS**. OPM Flow officially supports both, and most of the Python/Julia ecosystem is best tested on Linux. macOS works for development but OPM Flow binary availability is less consistent. Windows users should use WSL2.

### 0.2 Core runtime stack

Install the following in order:

```bash
# System dependencies
sudo apt update
sudo apt install -y build-essential cmake git curl wget \
    libboost-all-dev libopenblas-dev liblapack-dev \
    python3-dev python3-venv python3-pip

# Python environment
python3 -m venv ~/petrolumen-env
source ~/petrolumen-env/bin/activate
pip install --upgrade pip setuptools wheel

# Julia (for JutulDarcy)
curl -fsSL https://install.julialang.org | sh
# Restart shell, then:
julia -e 'using Pkg; Pkg.add(["Jutul", "JutulDarcy", "GeoEnergyIO"])'
```

### 0.3 MATLAB or GNU Octave

MRST requires MATLAB (preferred) or GNU Octave. If you do not have a MATLAB licence, install Octave:

```bash
sudo apt install -y octave
```

Download MRST from SINTEF and unzip into `~/mrst`:

```bash
wget https://www.sintef.no/globalassets/project/mrst/download/mrst-2026a.zip
unzip mrst-2026a.zip -d ~/mrst
```

The current release is MRST 2026a, released 20 May 2026, under GPL-3.0.

### 0.4 Repository structure

Create the project root:

```bash
mkdir -p ~/petrolumen/{src,tests,benchmarks,docs,data,notebooks}
cd ~/petrolumen
git init
```

Create `pyproject.toml` with the dependency set described in the architecture reference (pydantic, pint, FastAPI, pandas, xarray, pyarrow, resqpy, petres, geostatspy, welltest-pta, etc.).

### 0.5 Validation gate 0

Confirm each runtime works:

```bash
python -c "import sys; print(sys.version)"
julia -e 'using JutulDarcy; println("JutulDarcy OK")'
octave --eval "addpath(genpath('~/mrst')); mrstModule add core; disp('MRST OK')"
```

---

## Phase 1: Install and Validate the Classical Simulation Engines

### 1.1 OPM Flow

Install from the official PPA:

```bash
sudo add-apt-repository ppa:opm/ppa
sudo apt update
sudo apt install -y libopm-simulators-bin
```

The 2025.10 release supports Ubuntu 22.04 and 24.04 LTS. Verify:

```bash
flow --version
```

### 1.2 JutulDarcy.jl

JutulDarcy is MIT-licensed and fully differentiable, making it the primary engine for gradient-based workflows.

```bash
julia -e 'using Pkg; Pkg.add("JutulDarcy")'
julia -e 'using JutulDarcy; println(JutulDarcy.VERSION)'
```

### 1.3 MRST

MRST is the reference implementation for research-grade methods and the host of the ETH geothermal EDFM module and thermal-hfm.

```matlab
% In MATLAB or Octave
addpath(genpath('~/mrst'));
mrstModule add core ad-blackoil
```

### 1.4 open-DARTS (optional but recommended)

open-DARTS is a scalable parallel simulator for energy-transition applications (geothermal, CO₂, H₂). Install via pip:

```bash
pip install open-darts
```

open-DARTS is available for Python 3.9–3.12 on Linux and Windows.

### 1.5 Validation gate 1: run one benchmark on each engine

Download the OPM open datasets:

```bash
git clone https://github.com/OPM/opm-data.git ~/opm-data
```

Run SPE1 on OPM Flow:

```bash
cd ~/opm-data/spe1
flow SPE1.DATA
```

Run the same case on JutulDarcy:

```julia
using JutulDarcy, GeoEnergyIO
data = parse_data_file("SPE1.DATA")
model, state0, dt = setup_reservoir_model(data)
result = simulate_reservoir(state0, model, dt)
```

**Gate:** Both engines must produce cumulative oil production within 2% of the published SPE1 reference.

---

## Phase 2: Build the Engineering Calculation Layer

This phase gives you the non-simulation engineering calculations: PVT, well testing, geostatistics, grid handling, and RESQML interoperability.

### 2.1 pyResToolbox (PVT, IPR, material balance helpers)

```bash
pip install pyrestoolbox
```

The library provides PVT correlations, inflow performance, and simulation table generation. Start with:

```python
from pyrestoolbox import pyrestoolbox as rtb

# Example: Standing Rs
rs = rtb.rs_standing(psia=3000, t=180, api=35, gamma_g=0.75)
```

### 2.2 welltest-pta (pressure transient analysis)

```bash
pip install welltest-pta
```

The library provides a complete pipeline: parsing, event detection, Bourdet derivative, Horner plots, and parameter estimation.

```python
from welltest_pta import WellTest

wt = WellTest.from_csv("well_test.csv")
wt.detect_events()
wt.bourdet(L=0.2)
wt.horner()
params = wt.interpret(model="radial")
```

### 2.3 GeostatsPy (geostatistics)

```bash
pip install geostatspy
```

GeostatsPy is the Python reimplementation of GSLIB and the companion to Pyrcz's free e-book.

```python
import geostatspy.geostats as geostats
import geostatspy.GSLIB as GSLIB

vario = GSLIB.make_variogram(nug=0.0, nst=1, it1=1, cc1=1.0, a1=1000.0)
```

### 2.4 Petres (corner-point grids)

```bash
pip install petres
```

Petres constructs corner-point grids programmatically and reads/writes `.GRDECL` files.

```python
from petres.grids import CornerPointGrid

grid = CornerPointGrid.from_grdecl("model.grdecl")
print(grid.dimensions)
```

### 2.5 resqpy (RESQML interoperability)

```bash
pip install resqpy
```

resqpy is bp's pure-Python RESQML library for reading, writing, and modifying reservoir models.

```python
import resqpy.model as rq

model = rq.Model("reservoir.epc")
grid = model.grid()
extent = grid.extent_kji
```

### 2.6 Validation gate 2

Build a single Python module `petrolumen.reservoir.calculations` that exposes:

- a PVT function using pyResToolbox;
- a PTA interpretation using welltest-pta;
- a kriging estimate using GeostatsPy;
- a grid load using Petres;
- a RESQML open using resqpy.

Write one pytest per function. **Gate:** all tests pass on a clean environment.

---

## Phase 3: Data Model and API Skeleton

### 3.1 Define the core entities

Implement the pydantic models described in the architecture reference: `Project`, `FluidModel`, `RockModel`, `Grid`, `Well`, `Schedule`, `Case`, `Run`, `ResultSet`, `Test`.

Start with the minimum viable set: `Project`, `Case`, `Run`. Add the rest as needed.

### 3.2 PostgreSQL schema

Create the `reservoir` schema with the DDL from the architecture reference. If PostgreSQL is not yet available, start with SQLite for development and migrate later.

### 3.3 FastAPI endpoints

Implement the minimum API:

```
POST /v1/projects
POST /v1/projects/{id}/cases
POST /v1/cases/{id}/runs
GET  /v1/runs/{id}
GET  /v1/runs/{id}/results
```

The run endpoint must:

1. write an Eclipse deck from the case;
2. launch OPM Flow as a subprocess;
3. capture the log and exit code;
4. parse `.SMSPEC`/`.UNSMRY` into Parquet;
5. update the `Run` status.

### 3.4 Validation gate 3

From the API, create a project, create a case from the SPE1 deck, run it, and download the summary as Parquet. **Gate:** the Parquet file contains `FOPR`, `FOPT`, and `WBHP` time series.

---

## Phase 4: Benchmark Validation Suite

This is the phase that makes the tool credible. Do not skip it.

### 4.1 Download benchmarks

```bash
cd ~/opm-data
# SPE1, SPE9, SPE10, Norne are all in the OPM repository
ls spe1 spe9 spe10 norne
```

The Norne dataset is also available as an open Zenodo benchmark.

### 4.2 Implement regression tests

For each benchmark, write a pytest fixture that runs the deck and compares summary vectors against a reference:

```python
@pytest.mark.benchmark
def test_spe1(tmp_path):
    deck = copy_spe1(tmp_path)
    result = subprocess.run(["flow", str(deck)], cwd=tmp_path,
                            capture_output=True, text=True, timeout=600)
    assert result.returncode == 0
    summary = parse_summary(tmp_path / "SPE1.SMSPEC")
    assert abs(summary["FOPT"][-1] - reference["FOPT"][-1]) / reference["FOPT"][-1] < 0.02
```

### 4.3 Acceptance criteria

| Benchmark | Physics | Gate |
|---|---|---|
| SPE1 | Three-phase, gas coning | BHP and gas rate within 2% |
| SPE9 | Black-oil, 26 wells, faulted | Cumulative production within 2% |
| SPE10 | 60×220×85 heterogeneous | Water-cut within 3%; deterministic across runs |
| Norne | Real field | Summary vectors within agreed tolerance |

### 4.4 Validation gate 4

All four benchmarks pass in CI. **This is the point at which the classical workbench is defensible.**

---

## Phase 5: AI Surrogates — FNO/PINO for Norne

### 5.1 Clone the PhysicsNeMo Norne pipeline

The PhysicsNeMo repository contains a complete FNO/PINO pipeline for three-phase black-oil simulation on Norne, including the mixture-of-experts well model and ensemble Kalman inversion for history matching.

```bash
git clone https://github.com/NVIDIA/physicsnemo.git
cd physicsnemo/examples/reservoir_simulation/norne
```

### 5.2 Train the surrogate

Follow the repository's `Forward_problem_PINO.py` script. The pipeline expects:

- Norne simulation snapshots (generate with OPM Flow if not provided);
- well schedule and rate data;
- permeability and porosity fields.

### 5.3 Validate the surrogate

The published results report **R² > 0.99 for oil production** and roughly **10⁴× speedup** over OPM Flow for ensemble runs. Your acceptance gate should be:

- R² > 0.98 on held-out timesteps;
- relative error < 5% on cumulative production;
- inference time < 1 second per timestep.

### 5.4 Integrate as a plugin

Implement the `SurrogatePlugin` contract:

```python
class FNOReservoirSurrogate:
    def predict(self, inputs: dict) -> dict:
        ...
    def uncertainty(self, inputs: dict) -> dict:
        ...
```

**Gate:** the surrogate can replace OPM Flow inside a simple forecasting loop and produce a forecast within 5% of the full simulation.

---

## Phase 6: Differentiable UQ and History Matching

### 6.1 JutulDarcy adjoint gradients

JutulDarcy computes gradients of any quantity of interest with respect to all parameters through the adjoint method. The SPE1 gradient example is the starting point:

```julia
using JutulDarcy, GeoEnergyIO
data = parse_data_file("SPE1.DATA")
model, state0, dt = setup_reservoir_model(data)
# Define objective and parameters, then call gradient routine
```

### 6.2 ES-MDA in Python

Implement the ensemble smoother with multiple data assimilation using NumPy, as shown in the advanced reference. Test on SPE1 first, then SPE9, then Norne.

### 6.3 Validation gate 6

Run a history-matching loop on SPE1. **Gate:** the matched model reduces the weighted normalized RMSE by at least 50% relative to the prior, and the posterior ensemble re-run with OPM Flow reproduces the observations within measurement error.

---

## Phase 7: Reinforcement Learning for Closed-Loop Control

### 7.1 Clone DRL_CLRM

```bash
git clone https://github.com/yus-nas/DRL_CLRM.git
```

The repository implements deep RL for optimal well control under uncertain geology, with published NPV improvements of 15% (2D) and 33% (3D) over robust optimization.

### 7.2 Train a TD3 agent

Use Stable-Baselines3 (MIT-licensed) to train a TD3 agent on a reduced-order environment backed by your FNO surrogate or a coarse OPM Flow model.

### 7.3 Validation gate 7

On a 2D waterflood case, the RL agent must achieve NPV at least 4% above a reactive baseline and within 10% of the DRL_CLRM published result.

---

## Phase 8: Foundation-Model Forecasting

### 8.1 Install Lag-Llama

```bash
git clone https://github.com/time-series-foundation-models/lag-llama.git
cd lag-llama
pip install -e .
```

Lag-Llama is the first open-source foundation model for probabilistic time-series forecasting, with zero-shot and fine-tuning modes.

### 8.2 Zero-shot production forecasting

Feed a well's historical production series into the pre-trained model and generate a probabilistic forecast. Compare against a naive decline-curve baseline.

### 8.3 Fine-tune on analog wells

Fine-tune the model on a small set of analog wells from your basin. **Gate:** fine-tuned model reduces MAE by at least 10% relative to zero-shot.

---

## Phase 9: Agentic Workflows

### 9.1 pyResToolbox MCP server

```bash
git clone https://github.com/gabrielserrao/pyrestoolbox-mcp.git
cd pyrestoolbox-mcp
pip install -e .
```

This MCP server exposes 108 reservoir engineering tools to AI agents like Claude, covering PVT, well performance, nodal analysis, DCA, material balance, and simulation support.

### 9.2 open-darts-MCP

The open-darts-MCP project exposes the open-DARTS simulator through MCP. The published evaluation recommends **hybrid architectures** where deterministic code governs routine simulation operations and the LLM handles interpretation and diagnosis.

### 9.3 Build a safe agent layer

Implement three safeguards:

1. **Typed tool endpoints:** every MCP tool has a schema-validated input.
2. **Simulation sandbox:** agent-generated decks run in an isolated container with resource limits.
3. **Deterministic audit log:** every agent action records prompt, inputs, outputs, and artifacts.

### 9.4 Validation gate 9

Ask the agent (in natural language) to: "Run SPE1, report cumulative oil at 365 days, and compare with the reference." **Gate:** the agent selects the correct tool, runs the simulation, and returns a number within 2% of the reference, with the audit log showing the full chain.

---

## Phase 10: Energy-Transition Physics

### 10.1 CO₂ storage

Use OPM Flow for CO₂ storage simulation. Validate against the **FluidFlower benchmark** using the `pofff` Python package:

```bash
pip install pofff
```

The workflow uses OPM Flow for simulation and Everest for history matching, with the **Wasserstein distance** as the mismatch metric.

For **SPE11**, run Case B with OPM Flow and compare against the published dataset (DOI: 10.18419/DARUS-4750).

### 10.2 Hydrogen storage

Use open-DARTS for depleted-gas-field H₂ storage. Download the Bunter sandstone ensemble and run cyclic injection/production cases.

### 10.3 Geothermal

Use MRST with the **ETH** EDFM module for coupled hydrothermal simulation in fractured reservoirs. For mesh adaptivity, install **ICFERST**:

```bash
git clone https://github.com/ImperialCollegeLondon/multifluids_icferst.git
cd multifluids_icferst
./configure --enable-2d-adaptivity
make mp
```

ICFERST uses discontinuous control-volume finite elements with dynamic mesh optimisation.

### 10.4 Mesh coarsening and refinement

Install **pycopm** for OPM Flow deck-level coarsening, refinement, and submodel extraction:

```bash
pip install pycopm
pycopm coarsen -i 2 -j 2 -k 1 input.DATA output.DATA
```

### 10.5 Validation gate 10

- **CO₂:** FluidFlower plume geometry visually matches; Wasserstein distance below published threshold.
- **SPE11:** Case B converges and pressure/saturation evolution falls within the reference envelope.
- **Geothermal:** ETH benchmark relative error < 1%.
- **H₂:** recovery efficiency and CH₄ contamination fall within the open-DARTS ensemble range.

---

## Phase 11: Production Hardening

### 11.1 Testing

| Layer | Tool | Gate |
|---|---|---|
| Unit | pytest | >90% coverage on domain services |
| Integration | pytest + Docker | All API endpoints tested end-to-end |
| Benchmarks | pytest markers | SPE1/SPE9/SPE10/Norne pass every release |
| AI surrogates | pytest | R² > 0.98 on held-out data |
| Agentic | pytest + mock LLM | Tool selection correct on 20 golden prompts |

### 11.2 Packaging

- Build a Docker image that bundles OPM Flow, JutulDarcy, MRST, and the Python stack.
- Provide two installation profiles: `permissive-only` (excludes GPL engines) and `full` (includes OPM, MRST, pyResToolbox as optional backends).
- Publish on PyPI and as a container image.

### 11.3 Documentation

- **Physics docs:** every equation links to a reference (Dake, Peaceman, Lie, etc.).
- **API docs:** auto-generated from FastAPI/OpenAPI.
- **User guide:** one worked example per module (SPE1, FluidFlower, Bunter H₂).
- **Validation report:** a generated PDF showing benchmark results for the current release.

---

## Phase 12: Continuous Improvement

### 12.1 Quarterly cadence

| Quarter | Focus |
|---|---|
| Q1 | Classical workbench: Phases 0–4 |
| Q2 | AI surrogates and UQ: Phases 5–6 |
| Q3 | RL, forecasting, agents: Phases 7–9 |
| Q4 | Energy transition and hardening: Phases 10–11 |

### 12.2 What to watch

- **OPM Flow releases:** quarterly; pin versions and re-run benchmarks.
- **JutulDarcy releases:** check adjoint and history-matching changes.
- **New MCP servers:** the agentic ecosystem is moving fast; integrate only after audit.
- **Benchmark updates:** SPE11 and FluidFlower datasets evolve; track DOIs.

---

## Appendix A: Book-to-Module Mapping

| Book | Module it supports | How to use it |
|---|---|---|
| Dake, *Fundamentals* | Fluids, volumetrics, material balance | Implement equations as Python functions; test against SPE1/SPE9 |
| Dake, *Practice* | Workflow and engineering judgment | Encode as UI guidance and validation warnings, not automatic decisions |
| Ahmed, *Handbook* | Correlations, water influx | Cross-check pyResToolbox and custom implementations |
| McCain, *Properties* | PVT and lab matching | Use as the specification for the fluids module; implement compositional EOS tuning yourself |
| Lie, *MRST Introduction* | Simulation architecture | Build the plugin contract and deck writer around MRST's abstractions |
| Peaceman, *Numerical Simulation* | Discretisation and linear solvers | Validate OPM Flow/JutulDarcy against Peaceman's analytical solutions |
| Pyrcz, *Geostatistics in Python* | Geostats module | Follow the free e-book; GeostatsPy is the companion library |
| Pyrcz, *Applied ML in Python* | Surrogate and forecasting modules | Use as the ML training curriculum |
| Horne, *Modern Well Test* | PTA module | Implement models and validate against welltest-pta |
| Ganat, *Modern PTA* | PTA special cases | Add layered, fractured, and horizontal-well models |
| Lee & Wattenbarger, *Gas Reservoir* | Gas material balance and p/Z | Implement and test on gas benchmarks |
| Guo, *Production Engineering* | Nodal analysis | Integrate pynodal or implement IPR/VLP |
| Wheaton, *Economics* | Economics module | Implement NPV/IRR and fiscal models; keep judgment human |
| Satter et al., *Practical Enhanced* | EOR screening and integration | Implement screening criteria as advisory, not automatic |
| Newman, *Modern Handbook* | CO₂ and unconventional | Use as the specification for Phase 10 |
| Islam et al., *Advanced Simulation* | Emulators | Use FNO/PINN surrogates as the implementation path |
| SPEE Monograph 4 | Unconventional reserves | Implement probabilistic DCA and type-well workflows |

---

## Appendix B: Licensing Boundaries

| Component | Licence | Integration rule |
|---|---|---|
| OPM Flow | OSL-3.0 / GPL | External executable only |
| JutulDarcy.jl | MIT | Direct import via `juliacall` or subprocess |
| MRST | GPL-3.0 | External process only |
| open-DARTS | Open source | Direct import; check individual module licences |
| pyResToolbox | GPL-3.0 | Optional extra or subprocess |
| pyResToolbox MCP | GPL-3.0 | Optional agent layer |
| resqpy | Apache-2.0 | Direct import |
| Petres | LGPL | Direct import; dynamic linking |
| GeostatsPy | MIT | Direct import |
| welltest-pta | MIT | Direct import |
| Lag-Llama | Open source (Apache-2.0) | Direct import |
| DRL_CLRM | Open source | Research reference; re-implement as needed |

**Recommendation:** Ship PetroLumen itself under Apache-2.0 or MIT. Declare GPL engines as optional, user-installed backends discovered at runtime.

---

## Appendix C: Minimum Compute Requirements

| Phase | CPU | RAM | GPU | Storage |
|---|---|---|---|---|
| 0–4 | 8 cores | 32 GB | Not required | 50 GB |
| 5 (FNO training) | 16 cores | 64 GB | 24 GB VRAM recommended | 200 GB |
| 6–7 (UQ, RL) | 16 cores | 64 GB | Optional | 200 GB |
| 8–9 (foundation models) | 8 cores | 32 GB | 16 GB VRAM for fine-tuning | 100 GB |
| 10 (CO₂/H₂/geothermal) | 16 cores | 64 GB | Optional | 500 GB (SPE11) |

A single workstation with an NVIDIA RTX 4090 (24 GB) and 64 GB RAM is sufficient for Phases 0–9. Phase 10 benefits from a GPU with more memory for SPE11 Case C.

---

## Appendix D: What This Document Does Not Cover

This document is the **reservoir module only**. It does not cover:

- drilling engineering and well design;
- completions and artificial lift design;
- surface facilities and network modelling;
- fiscal regimes and portfolio optimisation;
- corporate reporting and investor packages.

Those are sibling modules. The reservoir module exposes its outputs (forecasts, pressures, rates, uncertainty ranges) through a stable API that sibling modules consume.

---

**End of document.**  
*Build in phases. Validate at every gate. Keep the physics transparent. The AI layer accelerates the work; it does not replace the engineering judgment.*