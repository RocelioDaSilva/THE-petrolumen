Here is a focused breakdown of what is achievable for the reservoir module of PetroLumen using **only free, open-source software and AI**.

### ⚙️ The Free AI Simulation Core

The foundation is a simulation engine that provides the physics and, crucially, the gradients needed for AI optimization.

*   **JutulDarcy.jl (MIT License)**: A high-performance, fully differentiable porous media simulator written in Julia. Its key feature is **automatic differentiation via the adjoint method**, which provides sensitivities of any output with respect to all model parameters. This enables gradient-based history matching and well-control optimization, is compatible with industry-standard `.DATA` input files, and supports black-oil, compositional, and geothermal models.
*   **OPM Flow (Open Source, GPU-accelerated)**: A fully implicit, industrial-complexity reservoir simulator that supports black-oil, CO₂ storage, and thermal simulation. The **gpu-ISTL** framework extends it with **GPU-accelerated linear solvers**, implementing a high-performance CPR+AMG solver stack on the GPU for large-scale simulation.

### 🧠 Free AI Surrogates: PINNs & Neural Operators

These tools let you build fast, AI-driven approximations of the physics, enabling real-time forecasting and massive ensemble runs.

*   **ReservoirFlow (Open Source)**: The first reservoir simulator built on **physics-informed neural network (PINN) models**. It allows you to compare and combine analytical, numerical, and neural solutions within a single Python library and supports backends like NumPy, JAX, and PyTorch.
*   **WellPINN (Open-Source Code)**: A published workflow using PINNs for accurate well representation in transient pressure diffusion problems. It uses a multi-level approach, with a global PINN refined by subdomain PINNs around the well, and all code and data are openly available.
*   **Fourier Neural Operator (FNO) for Norne (Open-Source)**: A complete, open pipeline for **three-phase black-oil simulation on the Norne field** using FNO and Physics-Informed Neural Operators (PINO). The results are impressive: autoregressive PINO surrogates achieve an **$R^2 > 0.99$ for oil production** and provide a **~$10^4\times$ speedup** over the OPM finite-volume simulator for ensemble runs.

### 🎮 Free AI for Control & Forecasting

This covers AI agents that learn optimal control policies and models that can forecast production with minimal data.

*   **Deep Reinforcement Learning (DRL) for Well Control (Open-Source)**: The `DRL_CLRM` repository contains the code for research on **deep reinforcement learning for optimal well control in subsurface systems with uncertain geology**. It implements agents (like SAC and PPO) that can learn control strategies directly from simulation data.
*   **Lag-Llama (Open-Source Foundation Model)**: The first open-source **foundation model for probabilistic time-series forecasting**. It is a small, 2.45M parameter model trained on a diverse set of public data (including energy) that provides **native uncertainty estimates** and supports **zero-shot forecasting**, meaning it can predict production from your wells without any additional training.

### 🤖 Free Agentic Workflows: Natural-Language Engineering

This is the frontier of usability, where LLMs are given tools to perform complex engineering tasks via natural language.

*   **pyResToolbox MCP Server (GPL-3.0)**: A production-ready **Model Context Protocol (MCP) server** that gives AI agents (like Claude) access to **108 reservoir engineering tools** from the `pyResToolbox` library. This allows an engineer to perform PVT analysis, generate IPR curves, and create simulation tables through a natural-language conversation, with the calculations executed by validated correlations.
*   **open-darts-MCP (Open-Source)**: An open-source initiative that designs **MCP servers for the open-DARTS simulator**. It investigates different architectures (RAG, schema-based, typed API exposure) to create reliable **agentic workflows** where LLMs can construct inputs and run simulations for geothermal, CO₂ storage, and other applications, all while keeping validation under user control.

### 💎 Summary

A fully functional, AI-augmented reservoir engineering suite can be built at zero software cost. You can use **JutulDarcy** for differentiable physics, **ReservoirFlow** and the **Norne FNO pipeline** for AI surrogates, **DRL_CLRM** for reinforcement learning control, **Lag-Llama** for foundation-model forecasting, and **pyResToolbox MCP** to tie it all together with natural-language agentic workflows. The primary investment is your time in integrating these tools and validating their results for your specific reservoirs.
