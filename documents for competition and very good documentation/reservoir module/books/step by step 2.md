# PetroLumen Reservoir Module: Exhaustive Step-by-Step Build Document

**Version 2.0 — Production-Grade Build Guide**  
**Scope:** Reservoir module only. Free and open-source toolchain with integrated AI acceleration.  
**Prerequisite:** Ubuntu 24.04 LTS (or 26.04 LTS), Python 3.11+, Git, and reservoir engineering fundamentals.

---

## How to Use This Document

This is the **definitive build sequence**. It assumes you are starting from a bare Ubuntu installation and ends with a validated, AI-augmented reservoir engineering workbench. Every phase has a **validation gate** — a concrete, testable criterion. Do not proceed past a gate until it passes.

The document is organized into **14 phases**. Phases 0–4 produce the classical workbench. Phases 5–9 add the AI layer. Phases 10–12 add energy-transition physics and production hardening. Phase 13 is continuous operation.

**Effort estimate for a solo developer:** 12–20 months for Phases 0–12, depending on prior experience and available compute. Phases 0–4 are achievable in 3–6 months and produce a defensible classical tool.

---

## Phase 0: Operating System and Core Runtime

### 0.1 Choose the correct Ubuntu version

OPM Flow 2026.04 officially supports **Ubuntu 24.04 LTS (Noble Numbat)** and **26.04 LTS (Resolute Racoon)** . Use 24.04 LTS for the widest ecosystem compatibility. If you use WSL2, ensure it is configured with Ubuntu 24.04 and systemd enabled.

### 0.2 Install system dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    build-essential cmake git curl wget unzip \
    libboost-all-dev libopenblas-dev liblapack-dev \
    libhdf5-dev libfftw3-dev libsuitesparse-dev \
    python3-dev python3-venv python3-pip \
    postgresql postgresql-contrib redis-server \
    docker.io docker-compose-v2 \
    graphviz libgraphviz-dev pkg-config
```

Enable Docker without sudo:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

### 0.3 Python environment

Create an isolated environment and install the base scientific stack:

```bash
python3 -m venv ~/petrolumen-env
source ~/petrolumen-env/bin/activate

pip install --upgrade pip setuptools wheel
pip install numpy scipy pandas xarray pyarrow \
    matplotlib seaborn plotly \
    scikit-learn torch torchvision torchaudio \
    transformers accelerate datasets \
    fastapi uvicorn pydantic pint \
    sqlalchemy alembic psycopg2-binary \
    pytest pytest-cov mypy ruff black \
    jupyterlab ipykernel
```

### 0.4 Julia installation

JutulDarcy.jl requires Julia 1.8 or newer . Install via juliaup:

```bash
curl -fsSL https://install.julialang.org | sh
# Restart shell, then:
julia -e 'using Pkg; Pkg.add(["Jutul", "JutulDarcy", "GeoEnergyIO", "GLMakie", "CairoMakie"])'
```

Verify:

```bash
julia -e 'using JutulDarcy; println("JutulDarcy loaded")'
```

### 0.5 MATLAB or GNU Octave for MRST

MRST requires MATLAB (preferred) or GNU Octave. If you have a MATLAB licence, ensure it is on the PATH. Otherwise:

```bash
sudo apt install -y octave
```

Download MRST 2026a (released 20 May 2026) from SINTEF:

```bash
wget https://www.sintef.no/globalassets/project/mrst/download/mrst-2026a.zip
unzip mrst-2026a.zip -d ~/mrst
```

Test in Octave:

```bash
octave --eval "addpath(genpath('~/mrst')); mrstModule add core ad-blackoil; disp('MRST OK')"
```

### 0.6 Validation gate 0

Run all four checks:

```bash
python -c "import torch, sklearn, fastapi; print('Python OK')"
julia -e 'using JutulDarcy; println("JutulDarcy OK")'
octave --eval "addpath(genpath('~/mrst')); mrstModule add core; disp('MRST OK')"
docker run --rm hello-world
```

**Gate:** all four print success messages.

---

## Phase 1: Classical Simulation Engines

### 1.1 OPM Flow 2026.04

Install from the official PPA:

```bash
sudo apt-add-repository ppa:opm/ppa
sudo apt update
sudo apt install -y libopm-simulators-bin
```

Alternatively, install the Python package:

```bash
pip install opm
```

Or pull the Docker image (includes GPU support for NVIDIA and AMD):

```bash
docker pull openporousmedia/opmreleases:2026.04
```

Verify:

```bash
flow --version
```

The 2026.04 release includes sequential energy equation solving, pressure/temperature-dependent brine viscosity, endpoint scaling for gas–water systems, and extended summary (ESMRY) files by default .

### 1.2 JutulDarcy.jl

JutulDarcy is installed in Phase 0.4. Verify the adjoint gradient capability with the SPE1 example:

```julia
using Jutul, JutulDarcy, GeoEnergyIO
data_pth = joinpath(GeoEnergyIO.test_input_file_path("SPE1"), "SPE1.DATA")
data = parse_data_file(data_pth)
model, state0, dt = setup_reservoir_model(data)
# The full gradient example is at examples/data_assimilation/spe1_gradients.jl
```

The JutulDarcy repository contains a complete adjoint gradient example for SPE1 .

### 1.3 MRST

MRST is installed in Phase 0.5. Test the black-oil module:

```matlab
addpath(genpath('~/mrst'));
mrstModule add ad-blackoil ad-core
% Run a simple SPE1 case
```

### 1.4 open-DARTS

open-DARTS is a scalable parallel simulator for hydrocarbon, geothermal, CO₂ sequestration, and hydrogen storage . Install via pip:

```bash
pip install open-darts
```

open-DARTS is available for Python 3.10–3.13 on Linux and Windows . Verify:

```python
import darts
print(darts.__version__)
```

### 1.5 ICFERST (optional, for adaptive mesh refinement)

ICFERST uses discontinuous control-volume finite elements with dynamic mesh optimisation. Installation instructions exist for Ubuntu, though they reference Ubuntu 18.04 and PETSc 3.8.3 . For modern Ubuntu, build PETSc from source first, then:

```bash
git clone https://github.com/ImperialCollegeLondon/multifluids_icferst.git
cd multifluids_icferst
./configure --enable-2d-adaptivity
make mp
```

ICFERST is optional; skip it if adaptive unstructured meshing is not immediately required.

### 1.6 Validation gate 1: run SPE1 on every engine

Download the OPM benchmark data:

```bash
git clone https://github.com/OPM/opm-data.git ~/opm-data
cd ~/opm-data/spe1
```

Run OPM Flow:

```bash
flow SPE1.DATA
```

Run JutulDarcy:

```julia
using JutulDarcy, GeoEnergyIO
data = parse_data_file("SPE1.DATA")
model, state0, dt = setup_reservoir_model(data)
result = simulate_reservoir(state0, model, dt)
```

Run MRST (in MATLAB/Octave):

```matlab
mrstModule add ad-blackoil
% Use the SPE1 deck shipped with MRST
```

**Gate:** Cumulative oil production (FOPT) at final time within 2% of the published SPE1 reference on at least two engines.

---

## Phase 2: Engineering Calculation Libraries

### 2.1 pyResToolbox (PVT, IPR, material balance)

```bash
pip install pyrestoolbox
```

The library provides correlations for PVT, inflow performance, and simulation table generation. Test Standing's Rs:

```python
from pyrestoolbox import pyrestoolbox as rtb
rs = rtb.rs_standing(psia=3000, t=180, api=35, gamma_g=0.75)
print(f"Rs = {rs:.2f} scf/STB")
```

### 2.2 welltest-pta (pressure transient analysis)

```bash
pip install welltest-pta
```

The library provides a complete pipeline with a command-line interface and a Python API .

```python
from welltest_pta import WellTest

wt = WellTest.from_file("DST.txt", cross_validate=True)
wt.print_summary()
wt.detect_events()
wt.bourdet(L=0.2)
wt.horner()
params = wt.interpret(model="radial")
```

### 2.3 GeostatsPy (geostatistics)

```bash
pip install geostatspy
```

GeostatsPy reimplements GSLIB variogram, kriging, and simulation routines in Python .

```python
import geostatspy.geostats as geostats
import geostatspy.GSLIB as GSLIB

vario = GSLIB.make_variogram(nug=0.0, nst=1, it1=1, cc1=1.0, a1=1000.0)
```

### 2.4 Petres (corner-point grids)

```bash
pip install petres
```

Petres reads and writes `.GRDECL` corner-point grids and supports property arrays .

```python
from petres.grids import CornerPointGrid

grid = CornerPointGrid.from_grdecl("model.grdecl", properties=["PORO", "PERMX"])
print(grid.dimensions)
```

### 2.5 resqpy (RESQML interoperability)

```bash
pip install resqpy
```

resqpy opens, queries, and writes RESQML `.epc` datasets .

```python
import resqpy.model as rq

model = rq.Model("reservoir.epc")
grid = model.grid()
extent = grid.extent_kji
print(f"Grid extent: {extent}")
```

### 2.6 pycopm (multi-fidelity model tailoring)

```bash
pip install pycopm
```

pycopm coarsens, refines, extracts submodels, and transforms OPM Flow decks . It requires OPM Flow 2024.10 or newer .

```bash
pycopm coarsen -i 2 -j 2 -k 1 input.DATA output.DATA
pycopm submodel --bbox 10 20 15 30 0 5 input.DATA sub.DATA
```

### 2.7 Validation gate 2

Write a Python module `petrolumen.calculations` that calls pyResToolbox, welltest-pta, GeostatsPy, Petres, resqpy, and pycopm. Write one pytest per library. **Gate:** all tests pass on a clean environment.

---

## Phase 3: Data Model and API Skeleton

### 3.1 PostgreSQL schema

Create the database and user:

```bash
sudo -u postgres psql
CREATE DATABASE petrolumen;
CREATE USER petrolumen WITH PASSWORD 'petrolumen';
GRANT ALL PRIVILEGES ON DATABASE petrolumen TO petrolumen;
\q
```

Apply the core DDL from the architecture reference. The minimum viable schema is:

- `project` (id, name, units, owner, created_at)
- `fluid_model` (id, project_id, kind, correlations, version)
- `grid` (id, project_id, format, dims, data_uri)
- `case` (id, project_id, grid_id, fluid_id, engine, solver_opts)
- `run` (id, case_id, deck_hash, engine_version, status, result_uri)

### 3.2 pydantic models

Implement typed domain objects. Start with `Project`, `Case`, `Run`, and `RunStatus`. Use `pint` for units:

```python
import pint
ureg = pint.UnitRegistry()
Q = ureg.Quantity

pressure = Q(3000, "psia").to("Pa")
```

### 3.3 FastAPI endpoints

Implement the minimum API:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

@app.post("/v1/projects")
def create_project(project: ProjectCreate) -> ProjectRead:
    ...

@app.post("/v1/cases")
def create_case(case: CaseCreate) -> CaseRead:
    ...

@app.post("/v1/runs")
def create_run(run: RunCreate) -> RunRead:
    ...

@app.get("/v1/runs/{run_id}")
def get_run(run_id: str) -> RunRead:
    ...
```

### 3.4 Job runner

Implement a Celery worker that:

1. writes an Eclipse deck from the `Case`;
2. launches OPM Flow or JutulDarcy as a subprocess;
3. captures the log and exit code;
4. parses `.SMSPEC`/`.UNSMRY` into Parquet;
5. updates the `Run` status in PostgreSQL.

### 3.5 Validation gate 3

From the API, create a project, create a case from SPE1, run it, and download the summary as Parquet. **Gate:** the Parquet file contains `FOPR`, `FOPT`, and `WBHP` time series, and the `Run` status is `succeeded`.

---

## Phase 4: Benchmark Validation Suite

### 4.1 Download benchmarks

SPE1, SPE9, SPE10, and Norne are all in the OPM data repository:

```bash
cd ~/opm-data
ls spe1 spe9 spe10 norne
```

Norne is also available as an open Zenodo benchmark (DOI: 10.5281/zenodo.复旦大学). The PhysicsNeMo Norne example uses a 46 × 112 × 22 corner-point grid .

### 4.2 Implement regression tests

For each benchmark, write a pytest fixture that runs the deck and compares summary vectors:

```python
@pytest.mark.benchmark
def test_spe1(tmp_path):
    deck = tmp_path / "SPE1.DATA"
    deck.write_text(SPE1_DECK)
    result = subprocess.run(["flow", str(deck)], cwd=tmp_path,
                            capture_output=True, text=True, timeout=600)
    assert result.returncode == 0
    summary = parse_summary(tmp_path / "SPE1.SMSPEC")
    assert abs(summary["FOPT"][-1] - REFERENCE["FOPT"][-1]) / REFERENCE["FOPT"][-1] < 0.02
```

### 4.3 Acceptance criteria

| Benchmark | Physics | Gate |
|---|---|---|
| **SPE1** | Three-phase, gas coning | BHP and gas rate within 2% |
| **SPE9** | Black-oil, 26 wells, faulted | Cumulative production within 2% |
| **SPE10** | 60×220×85 heterogeneous | Water-cut within 3%; deterministic across runs |
| **Norne** | Real field, complex geology | Summary vectors within agreed tolerance |

### 4.4 Validation gate 4

All four benchmarks pass in CI on every commit. **This is the point at which the classical workbench is defensible.** Tag the release `v0.1.0-classical`.

---

## Phase 5: AI Surrogates — FNO/PINO for Norne

### 5.1 Clone the PhysicsNeMo Norne pipeline

The PhysicsNeMo repository contains a complete end-to-end pipeline for three-phase black-oil simulation on Norne, combining:

- a **Fourier Neural Operator (FNO/PINO)** surrogate of the black-oil PDE system;
- a **Cluster–Classify–Regress (CCR) Mixture-of-Experts** well-rate model;
- an **Adaptive Regularised Ensemble Kalman Inversion (α-REKI)** for history matching .

```bash
git clone https://github.com/clementetienam/physicsnemo.git
cd physicsnemo/examples/reservoir_simulation/norne
```

The full pipeline is orchestrated by `scripts/docker/startup.sh` .

### 5.2 Generate training data

If Norne simulation snapshots are not included, generate them with OPM Flow:

```bash
flow NORNE.DATA --output-dir=norne_runs
```

The pipeline expects pressure, saturation, and well-rate outputs at each timestep.

### 5.3 Train the FNO/PINO surrogate

Run the forward problem script:

```bash
python src/Forward_problem_PINO.py --config DECK_CONFIG.yaml
```

The composite training objective combines data loss with physics-residual losses derived from the black-oil equations .

### 5.4 Validate the surrogate

Published results report **R² > 0.99 for oil production** and roughly **10⁴× speedup** over OPM Flow for ensemble runs. Your gate:

- R² > 0.98 on held-out timesteps;
- relative error < 5% on cumulative production;
- inference time < 1 second per timestep.

### 5.5 Integrate as a plugin

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

JutulDarcy computes gradients of any quantity of interest with respect to all parameters through the adjoint method . Start with the SPE1 gradient example:

```julia
using Jutul, JutulDarcy, GeoEnergyIO
data = parse_data_file("SPE1.DATA")
model, state0, dt = setup_reservoir_model(data)
# Define objective, parameters, and call gradient routine
```

The full example is at `examples/data_assimilation/spe1_gradients.jl` in the JutulDarcy repository .

### 6.2 ES-MDA in Python

Implement the ensemble smoother with multiple data assimilation using NumPy:

```python
def es_mda_update(M, D, Cd, alpha, R=None):
    Ne = M.shape[0]
    Cmd = np.cov(M.T, D.T)[:M.shape[1], M.shape[1]:]
    Cdd = np.cov(D.T)
    K = Cmd @ np.linalg.inv(Cdd + alpha * Cd)
    if R is not None:
        K = R * K
    noise = np.random.multivariate_normal(
        np.zeros(D.shape[1]), alpha * Cd, size=Ne
    )
    return M + (K @ (d_obs - D + noise).T).T
```

### 6.3 Validation gate 6

Run a history-matching loop on SPE1. **Gate:** the matched model reduces the weighted normalized RMSE by at least 50% relative to the prior, and the posterior ensemble re-run with OPM Flow reproduces the observations within measurement error.

---

## Phase 7: Reinforcement Learning for Closed-Loop Control

### 7.1 Clone DRL_CLRM

The `DRL_CLRM` repository implements deep RL for optimal well control under uncertain geology, with published NPV improvements of 15% (2D) and 33% (3D) over robust optimization .

```bash
git clone https://github.com/yus-nas/DRL_CLRM.git
cd DRL_CLRM
pip install -r requirements.txt
```

### 7.2 Train a TD3 agent

Use Stable-Baselines3 (MIT-licensed) to train a TD3 agent on a reduced-order environment backed by your FNO surrogate or a coarse OPM Flow model:

```python
from stable_baselines3 import TD3
from petrolumen.rl import ReservoirEnv

env = ReservoirEnv(case, surrogate=fno_surrogate)
model = TD3("MlpPolicy", env, learning_rate=3e-4,
            buffer_size=1_000_000, batch_size=256,
            gamma=0.99, tau=0.005, policy_delay=2)
model.learn(total_timesteps=1_000_000)
model.save("td3_reservoir_agent")
```

### 7.3 Validation gate 7

On a 2D waterflood case, the RL agent must achieve NPV at least 4% above a reactive baseline and within 10% of the DRL_CLRM published result.

---

## Phase 8: Foundation-Model Forecasting

### 8.1 Install Lag-Llama

Lag-Llama is the first open-source foundation model for probabilistic time-series forecasting . It supports zero-shot forecasting on any frequency and fine-tuning on domain data.

```bash
git clone https://github.com/time-series-foundation-models/lag-llama.git
cd lag-llama
pip install -r requirements.txt
```

Or install via the `zsfm` package:

```bash
pip install zsfm
```

### 8.2 Zero-shot production forecasting

Feed a well's historical production series into the pre-trained model and generate a probabilistic forecast:

```python
from zsfm import LagLlamaForecaster

forecaster = LagLlamaForecaster.from_pretrained("lag-llama")
forecast = forecaster.predict(context=production_history, prediction_length=365)
```

### 8.3 Fine-tune on analog wells

Fine-tune the model on a small set of analog wells from your basin. The paper recommends benchmarking zero-shot performance first, then fine-tuning if necessary .

**Gate:** fine-tuned model reduces MAE by at least 10% relative to zero-shot on held-out wells.

---

## Phase 9: Agentic Workflows

### 9.1 pyResToolbox MCP server

The pyResToolbox MCP server gives AI agents access to **108 production-ready reservoir engineering tools** covering PVT, well performance, nodal analysis, DCA, material balance, simulation support, brine properties, geomechanics, and heterogeneity analysis . It is GPL-3.0 licensed and built on FastMCP .

```bash
git clone https://github.com/gabrielserrao/pyrestoolbox-mcp.git
cd pyrestoolbox-mcp
pip install -e .
```

Configure your MCP client (e.g., Claude Desktop) to launch the server.

### 9.2 open-DARTS MCP integration

The open-DARTS repository exposes its configuration grammar and physics/evaluator plugins through an MCP server, giving LLM agents programmatic access to the model configuration schema . This enables agent-driven construction of open-DARTS simulation cases.

### 9.3 Build a safe agent layer

Implement three safeguards:

1. **Typed tool endpoints:** every MCP tool has a schema-validated input.
2. **Simulation sandbox:** agent-generated decks run in an isolated Docker container with CPU and memory limits.
3. **Deterministic audit log:** every agent action records the prompt, inputs, outputs, and generated artefacts in PostgreSQL.

### 9.4 Validation gate 9

Ask the agent (in natural language): “Run SPE1, report cumulative oil at 365 days, and compare with the reference.” **Gate:** the agent selects the correct tool, runs the simulation, and returns a number within 2% of the reference, with the audit log showing the full chain from prompt to result.

---

## Phase 10: Energy-Transition Physics

### 10.1 CO₂ storage — FluidFlower

The `pofff` package (Python OPM Flow FluidFlower) is an open-source image-based history-matching framework for the International FluidFlower benchmark . It generates OPM Flow, ERT, and Everest input, runs simulations, and performs history matching .

```bash
pip install pofff
```

Run the workflow:

```python
import pofff

case = pofff.FluidFlowerCase(
    deck="fluidflower.DATA",
    observations="fluidflower_obs.h5",
    metric="wasserstein",
)
result = pofff.history_match(case, max_evals=200)
pofff.plot_match(result)
```

The workflow uses the **Wasserstein distance** as the mismatch metric for multiphase, multicomponent flow data .

### 10.2 CO₂ storage — SPE11

Run SPE11 Case B with OPM Flow:

```bash
flow spe11b.DATA
```

Compare pressure and saturation evolution against the published dataset (DOI: 10.18419/DARUS-4750). **Gate:** convergence within documented tolerance and visual match of the plume geometry.

### 10.3 Hydrogen storage — open-DARTS Bunter models

Open-DARTS models of hydrogen storage in depleted gas fields of the Bunter sandstone are available as an ensemble of 32 geological models. Download and run:

```bash
git clone https://gitlab.com/open-darts/h2-bunter.git
cd h2-bunter
python main_run.py --model bunter_1p2c_reference --cycles 10
```

**Gate:** H₂ recovery efficiency and CH₄ contamination fall within the ensemble range.

### 10.4 Geothermal — ETH EDFM and ICFERST

The ETH module for MRST implements embedded discrete fracture models (EDFM) for coupled hydrothermal processes in fractured geothermal reservoirs. Install the MRST module and run the benchmark cases.

For adaptive mesh refinement, use ICFERST if installed. **Gate:** ETH benchmark relative error < 1%.

### 10.5 Mesh coarsening and refinement — pycopm

pycopm is already installed in Phase 2.6. Use it to generate multi-fidelity model hierarchies:

```bash
pycopm coarsen -i 2 -j 2 -k 1 input.DATA output.DATA
pycopm submodel --bbox 10 20 15 30 0 5 input.DATA sub.DATA
```

### 10.6 Validation gate 10

All energy-transition benchmarks pass their respective gates. Tag the release `v1.0.0-energy-transition`.

---

## Phase 11: Testing and Quality Assurance

### 11.1 Test pyramid

| Layer | Tool | Gate |
|---|---|---|
| **Unit** | pytest | >90% coverage on domain services |
| **Integration** | pytest + Docker | All API endpoints tested end-to-end |
| **Benchmarks** | pytest markers | SPE1/SPE9/SPE10/Norne pass every release |
| **AI surrogates** | pytest | R² > 0.98 on held-out data |
| **Agentic** | pytest + mock LLM | Tool selection correct on 20 golden prompts |
| **Energy transition** | pytest | FluidFlower, SPE11, Bunter, ETH pass |

### 11.2 Static analysis

Run on every commit:

```bash
ruff check src/
black --check src/
mypy --strict src/petrolumen/core/
```

### 11.3 CI pipeline

Use GitHub Actions or GitLab CI with a matrix:

- Ubuntu 24.04 and 26.04;
- Python 3.11, 3.12, 3.13;
- With and without GPU.

The pipeline must build a Docker image that bundles OPM Flow, JutulDarcy, MRST, and the Python stack.

### 11.4 Validation gate 11

CI is green on all supported platforms. The Docker image runs SPE1 successfully on a clean machine.

---

## Phase 12: Documentation and Distribution

### 12.1 Physics documentation

Every equation in the code must link to a reference. Generate a `physics/` directory with:

- black-oil conservation equations (Dake, Peaceman);
- material balance (Havlena–Odeh);
- PTA (Horne, Bourdet);
- geostatistics (Pyrcz, Deutsch);
- discretisation and Newton–Raphson (Lie, Peaceman).

### 12.2 API documentation

Auto-generate OpenAPI documentation from FastAPI. Publish at `/docs`.

### 12.3 User guide

Write one worked example per module:

- SPE1 for classical simulation;
- Norne for AI surrogates;
- FluidFlower for CO₂;
- Bunter for H₂;
- ETH for geothermal.

### 12.4 Validation report

Generate a PDF that shows benchmark results for the current release. Include:

- SPE1/SPE9/SPE10/Norne comparison plots;
- FNO surrogate R² and error metrics;
- FluidFlower Wasserstein distance;
- Bunter H₂ recovery statistics.

### 12.5 Packaging

Publish on PyPI:

```bash
pip install petrolumen[classical]      # OPM Flow + Python only
pip install petrolumen[ai]            # + PyTorch, transformers
pip install petrolumen[full]          # + GPL engines (OPM, MRST, pyResToolbox)
```

Publish a Docker image:

```bash
docker pull petrolumen/petrolumen:latest
```

### 12.6 Validation gate 12

A new user can install PetroLumen, run SPE1, and reproduce the reference result in under 30 minutes. The documentation covers every error message they might encounter.

---

## Phase 13: Continuous Operation

### 13.1 Quarterly cadence

| Quarter | Focus |
|---|---|
| **Q1** | Classical workbench: Phases 0–4 |
| **Q2** | AI surrogates and UQ: Phases 5–6 |
| **Q3** | RL, forecasting, agents: Phases 7–9 |
| **Q4** | Energy transition and hardening: Phases 10–12 |

### 13.2 What to monitor

- **OPM Flow releases:** quarterly; pin versions and re-run benchmarks. The 2026.04 release adds sequential energy solving and brine viscosity support .
- **JutulDarcy releases:** check adjoint and history-matching changes.
- **PhysicsNeMo Norne:** track the α-REKI updates and new surrogate architectures .
- **MCP ecosystem:** new reservoir MCP servers appear frequently; audit before integration.
- **Benchmark datasets:** FluidFlower and SPE11 DOIs are updated; re-validate.

---

## Appendix A: Book-to-Module Mapping

| Book | Module | Implementation path |
|---|---|---|
| Dake, *Fundamentals* | Fluids, volumetrics, material balance | pyResToolbox + custom Python; validate on SPE1/SPE9 |
| Dake, *Practice* | Workflow and judgment | Encode as UI guidance and validation warnings |
| Ahmed, *Handbook* | Correlations, water influx | Cross-check pyResToolbox; implement aquifer models |
| McCain, *Properties* | PVT and lab matching | Use as spec; implement compositional EOS tuning with SciPy |
| Lie, *MRST Introduction* | Simulation architecture | Build plugin contract around MRST abstractions |
| Peaceman, *Numerical Simulation* | Discretisation, linear solvers | Validate OPM Flow/JutulDarcy against analytical solutions |
| Pyrcz, *Geostatistics in Python* | Geostats module | Follow the free e-book; GeostatsPy is the companion |
| Pyrcz, *Applied ML in Python* | Surrogate and forecasting | Use as ML curriculum; PyTorch/scikit-learn |
| Horne, *Modern Well Test* | PTA | welltest-pta + custom models |
| Ganat, *Modern PTA* | PTA special cases | Add layered, fractured, horizontal-well models |
| Lee & Wattenbarger, *Gas Reservoir* | Gas material balance, p/Z | Implement and test on gas benchmarks |
| Guo, *Production Engineering* | Nodal analysis | pynodal or custom IPR/VLP |
| Wheaton, *Economics* | Economics | Implement NPV/IRR; keep judgment human |
| Satter et al., *Practical Enhanced* | EOR screening | Implement screening criteria as advisory |
| Newman, *Modern Handbook* | CO₂ and unconventional | Use as spec for Phase 10 |
| Islam et al., *Advanced Simulation* | Emulators | FNO/PINN surrogates |
| SPEE Monograph 4 | Unconventional reserves | Probabilistic DCA and type-well workflows |

---

## Appendix B: Licensing Boundaries

| Component | Licence | Integration rule |
|---|---|---|
| **OPM Flow** | OSL-3.0 / GPL | External executable only |
| **JutulDarcy.jl** | MIT | Direct import via `juliacall` or subprocess |
| **MRST** | GPL-3.0 | External process only |
| **open-DARTS** | Open source | Direct import; check module licences |
| **pyResToolbox** | GPL-3.0 | Optional extra or subprocess |
| **pyResToolbox MCP** | GPL-3.0 | Optional agent layer |
| **resqpy** | Apache-2.0 | Direct import |
| **Petres** | LGPL | Direct import; dynamic linking |
| **GeostatsPy** | MIT | Direct import |
| **welltest-pta** | MIT | Direct import |
| **Lag-Llama** | Apache-2.0 | Direct import |
| **DRL_CLRM** | Open source | Research reference; re-implement as needed |

Ship PetroLumen under Apache-2.0 or MIT. Declare GPL engines as optional, user-installed backends discovered at runtime.

---

## Appendix C: Compute Requirements

| Phase | CPU | RAM | GPU | Storage |
|---|---|---|---|---|
| **0–4** | 8 cores | 32 GB | Not required | 50 GB |
| **5 (FNO training)** | 16 cores | 64 GB | 24 GB VRAM recommended | 200 GB |
| **6–7 (UQ, RL)** | 16 cores | 64 GB | Optional | 200 GB |
| **8–9 (foundation models)** | 8 cores | 32 GB | 16 GB VRAM for fine-tuning | 100 GB |
| **10 (CO₂/H₂/geothermal)** | 16 cores | 64 GB | Optional | 500 GB (SPE11) |

A single workstation with an NVIDIA RTX 4090 (24 GB) and 64 GB RAM is sufficient for Phases 0–9. Phase 10 benefits from a GPU with more memory for SPE11 Case C.

---

## Appendix D: Troubleshooting Common Failures

| Symptom | Likely cause | Fix |
|---|---|---|
| OPM Flow not found after PPA install | PPA not updated | `sudo apt update && sudo apt install libopm-simulators-bin` |
| JutulDarcy precompilation hangs | Missing system libraries | Install `libopenblas-dev liblapack-dev`; restart Julia |
| MRST module not found | Path not set | `addpath(genpath('~/mrst'))` before `mrstModule add` |
| open-DARTS pip install fails | Python version mismatch | Use Python 3.10–3.13; create a fresh venv |
| pyResToolbox MCP tools not appearing | MCP client not configured | Check the server is running and the client JSON points to the correct command |
| FNO training diverges | Learning rate too high | Reduce to `1e-4`; check physics-residual loss scaling |
| Lag-Llama zero-shot poor | Context length too short | Increase context to 64–128; benchmark before fine-tuning |
| pycopm coarsening fails | OPM Flow version too old | Upgrade to OPM Flow 2024.10 or newer |

---

**End of document.**

*Build in phases. Validate at every gate. Keep the physics transparent. The AI layer accelerates the work; it does not replace the engineering judgment.*