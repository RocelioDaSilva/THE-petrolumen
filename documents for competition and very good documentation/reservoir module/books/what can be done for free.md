From the full roadmap we mapped out, the honest answer is that a **very substantial portion of the AI-augmented reservoir module can be built and run entirely for free**. The frontier is no longer gated by software licences — it is gated by your time, compute, and validation effort. Here is the synthesis of what is achievable, phase by phase, with the specific free tools that make it possible.

---

### 🧱 The Free Foundation: Classical Simulation + Differentiable Core

Before any AI layer, you need a working physics engine. The free stack delivers two complementary backends:

- **OPM Flow** is an open-source, fully implicit, industrial-complexity reservoir simulator. It already has **GPU-accelerated linear solvers** (gpu-ISTL) and **autotuned GPU ILU(0)/DILU preconditioners** integrated into the main codebase, with CPR-based solvers in active development. This gives you a free, GPU-capable black-oil and compositional engine.
- **JutulDarcy.jl** is a **fully differentiable** porous-media simulator written in Julia, MIT-licensed, and designed from the ground up for sensitivities and extensibility. It supports CO₂ sequestration, gas/H₂ storage, and oil/gas fields, and its compositional simulator has been matched against commercial offerings and MRST. This is the engine that makes gradient-based optimization and data assimilation possible without finite differences.

**What this enables for free:** Full-field simulation, adjoint-based sensitivity analysis, and the foundation for every AI method that needs a differentiable forward model.

---

### 🤖 AI Surrogates: Physics-Informed Neural Networks & Neural Operators

This is where the free AI layer becomes genuinely powerful.

**Physics-Informed Neural Networks (PINNs)** for reservoir modelling are openly available. **WellPINN** is a published, open-access workflow that uses PINNs to solve transient fluid-flow problems with accurate well representation across three orders of magnitude in scale, and all code and data are openly released. A separate MIT-licensed PINN tutorial repository specifically targets reservoir modelling in petroleum engineering. These give you a free, code-first entry point for building real-time surrogate models.

**Fourier Neural Operators (FNOs)** are even more directly applicable. **PhysicsNeMo** hosts a complete, open pipeline for **three-phase black-oil simulation on the Norne field**, combining an FNO/PINO surrogate of the PDE system with a mixture-of-experts well-rate model and adaptive ensemble Kalman inversion for history matching. This is not a toy example — it is an end-to-end reservoir-engineering workflow using operator learning, available as open code. There are also FNO examples for CO₂ plume migration and physics-informed FNOs for parametric subsurface flow learning.

**What this enables for free:** Fast surrogate models that can replace full simulation inside optimization loops, history matching, and digital-twin updates — trained on your own data or on open benchmark datasets.

---

### 🎮 Reinforcement Learning for Closed-Loop Control

Deep RL for well control is fully reproducible with free tools. A publicly available GitHub repository implements **DRL for closed-loop reservoir management**, with published results showing an **NPV increase of 15% (2D cases) and 33% (3D cases)** relative to robust optimization over prior models. The underlying RL algorithms are available through **Stable-Baselines3** (MIT-licensed), which provides production-grade TD3, PPO, and SAC implementations for continuous control actions.

**What this enables for free:** Training an RL agent to optimize well schedules, injection rates, or choke settings against a simulator or surrogate, with published benchmark performance to validate against.

---

### 🧠 Time-Series Foundation Models for Forecasting

The time-series foundation model ecosystem is largely open. **Lag-Llama** is an open probabilistic forecasting model trained on a curated subset of public time-series repositories spanning energy, traffic, weather, and economics — directly relevant to production forecasting. **OpenLTM** provides a full pipeline for developing and evaluating large time-series models, and **Toto 2.0** has released open-weight forecasting models with state-of-the-art benchmark results.

**What this enables for free:** Zero-shot or few-shot production forecasting, well-log imputation, and anomaly detection without training a model from scratch.

---

### 🕹️ Agentic Workflows: Natural-Language-Driven Simulation

This is the most recent and most surprising free capability. Multiple open projects now expose reservoir simulators to LLM agents through the **Model Context Protocol (MCP)**:

- **pyResToolbox MCP Server** gives AI agents access to **108 production-ready reservoir-engineering tools** covering PVT, well performance, nodal analysis, DCA, material balance, simulation support, geomechanics, and brine properties — all under a GPL-3.0 licence.
- **RE-Agent** is a Streamlit-based conversational interface built on the pyResToolbox MCP server, performing 100+ specialized engineering functions through natural language.
- **open-darts-MCP** is an MCP integration for the open-DARTS simulator, with a published evaluation of four agent architectures. The key finding: **hybrid architectures where deterministic code governs routine simulation operations and the LLM is reserved for interpretation, diagnosis, and open-ended reasoning are the most reliable** — and this enables **smaller, locally hosted LLMs** to complete structured simulation subtasks reliably.
- **GeoView** is an open-source web application for reservoir simulation, optimization, and visualization, **powered by an AI agent**, using JutulDarcy as the simulation backend and supporting ECLIPSE-format input decks.

**What this enables for free:** A conversational reservoir-engineering assistant that can run PVT calculations, generate simulation tables, perform nodal analysis, and drive a simulator — using locally hosted or free-tier LLMs, with deterministic validation boundaries.

---

### 🗺️ The Free AI Roadmap at a Glance

| Phase | Free AI Capability | Primary Open Tools |
|---|---|---|
| **Classical core** | GPU-capable black-oil/compositional simulation | OPM Flow (gpu-ISTL), JutulDarcy.jl |
| **Differentiable UQ** | Adjoint gradients, ensemble data assimilation | JutulDarcy.jl, NumPy ES-MDA |
| **AI surrogates** | PINNs and FNOs for real-time forecasting | WellPINN, PhysicsNeMo (Norne FNO/PINO) |
| **Reinforcement learning** | Closed-loop well control with published NPV gains | Stable-Baselines3, DRL_CLRM repository |
| **Foundation models** | Zero-shot/few-shot production forecasting | Lag-Llama, OpenLTM, Toto 2.0 |
| **Agentic workflows** | Natural-language simulation and engineering calculations | pyResToolbox MCP, RE-Agent, open-darts-MCP, GeoView |

---

### ⚠️ The Honest Caveat

What is **not** free is the part that separates a demo from a deployable tool: **validation on your specific reservoirs, compute for large ensembles, and the engineering judgment to know when a surrogate is lying to you**. The free tools give you the mathematics and the code. The Norne FNO pipeline, the DRL_CLRM results, and the WellPINN workflows all come with published benchmarks, which gives you a validation starting point — but adapting them to your data, your fault blocks, and your operational constraints is where the real work lives.

The frontier is open. The licence barrier is gone. What remains is the engineering.