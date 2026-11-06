Building a full reservoir engineering tool suite means going beyond classical simulation—it requires covering the entire workflow from subsurface characterization to economic forecasting. The books below are organized by the functional modules of a comprehensive suite, so you can see exactly which resources support each part of the software you're building.

### 🧱 Core Reservoir Engineering & Physics
This is the foundation layer—the physics your engine must encode.

*   **Fundamentals of Reservoir Engineering** by L.P. Dake: The standard for basic reservoir physics and material balance.
*   **The Practice of Reservoir Engineering** by L.P. Dake: A more advanced, practical follow-up covering field development and reservoir management.
*   **Reservoir Engineering Handbook** by Tarek Ahmed: A broad reference for engineering calculations and workflows.
*   **Integrated Reservoir Engineering: From Fundamentals to Field Development** by D. Nathan Meehan: A modern, systems-based text that covers material balance, pressure transient analysis, well performance, EOR, and economic evaluation, **with downloadable Python code** for implementation.
*   **The Properties of Petroleum Fluids** by William D. McCain, Jr.: Essential for implementing PVT calculations and fluid property modeling.
*   **Gas Reservoir Engineering** by John Lee and Robert A. Wattenbarger: Necessary if your suite handles gas reservoirs, which have distinct physics from oil.

### ⚙️ Numerical Simulation & Algorithms
These resources teach you how to discretize the physics and build the solver—the core computational engine.

*   **An Introduction to Reservoir Simulation Using MATLAB/GNU Octave** by Knut-Andreas Lie: The most direct guide to implementing a simulator using an open-source framework (MRST).
*   **Advanced Modelling with the MATLAB Reservoir Simulation Toolbox (MRST)** edited by Knut-Andreas Lie and Olav Møyner: Extends the introductory text into advanced numerical methods and modern workflows.
*   **Fundamentals of Numerical Reservoir Simulation** by Donald W. Peaceman: The classic theoretical reference for the numerical solution of PDEs in reservoir simulation.
*   **Basic Applied Reservoir Simulation** by Turgay Ertekin, Jamal H. Abou-Kassem, and Gregory R. King: Provides comprehensive coverage of simulation fundamentals from an engineering perspective.
*   **Principles of Applied Reservoir Simulation** by John R. Fanchi: Bridges the gap between mathematical theory and engineering application.

### 🗺️ Geostatistics & Geological Modeling
A complete suite needs to ingest and model geological data before simulation can begin.

*   **Geostatistical Reservoir Modeling** by Michael J. Pyrcz and Clayton V. Deutsch: A leading text on building static reservoir models.
*   **Applied Geostatistics in Python: A Hands-on Guide with GeostatsPy** by Michael J. Pyrcz: **Free e-book** that uses Python code to teach practical geostatistics, ideal for directly building software modules.
*   **Geostatistics: Modeling Spatial Uncertainty** by Jean-Paul Chilès and Pierre Delfiner: A rigorous mathematical reference for advanced uncertainty quantification.

### 📈 Well Testing & Pressure Transient Analysis
This is a critical diagnostic module for any production engineer.

*   **Modern Pressure Transient Analysis of Petroleum Reservoirs** by Tarek Al-Arbi Omar Ganat: A current, practical reference covering layered reservoirs, fractured reservoirs, horizontal wells, and modern best practices.
*   **Pressure Transient Testing** (SPE Monograph): Explains the theoretical bases of commercial well-test-analysis software, helping you replicate those capabilities.
*   **Modern Well Test Analysis: A Computer-Aided Approach** by Roland N. Horne: Directly relevant to building software-based interpretation workflows.

### 🏭 Production Engineering & Optimization
A reservoir suite is incomplete without tools for well performance and surface network integration.

*   **Petroleum Production Engineering: A Computer-Assisted Approach** by Boyun Guo et al.: Focuses on implementing production engineering calculations in software.
*   **Production Optimization of Oil and Gas Fields Using NeqSim** by Equinor: Demonstrates how to build an open-source tool for integrated production optimization from reservoir to market.

### 💰 Petroleum Economics & Risk Analysis
Engineers need to evaluate the commercial viability of their forecasts.

*   **Fundamentals of Applied Reservoir Engineering: Appraisal, Economics and Optimization** by Wil Wheaton: Integrates reservoir appraisal, economics, and development optimization into a single workflow.
*   **Practical Enhanced Reservoir Engineering** by Abdus Satter, Ghulam M. Iqbal, and James L. Buchwalter: Includes sections on petroleum economics, integrated modeling, and risk/uncertainty analysis alongside simulation fundamentals.
*   **Petroleum Engineering & Economics Essentials** by Eastex Petroleum: A how-to manual that serves as a companion to a software suite covering reservoir, production, and economics programs.

### 🤖 Machine Learning & Data Analytics
Modern suites increasingly incorporate data-driven methods for forecasting and history matching.

*   **Machine Learning in the Oil and Gas Industry** by Yogendra N. Pandey et al.: Provides Python-based implementations for reservoir engineering, production forecasting, and assisted history matching.
*   **Applied Machine Learning in Python: A Hands-on Guide with Code** by Michael J. Pyrcz: **Free e-book** that teaches ML through coding examples, useful for embedding analytics into your suite.
*   **Python for Oil & Gas: Data Science, Engineering Analytics, and AI** by Johnpaul Okeke: Covers reservoir simulation, nodal analysis, and production optimization from a Python data-science perspective.

### 💻 Software Architecture & Python Implementation
These books help you turn the domain logic into a maintainable, scalable application.

*   **Mastering Petroleum Engineering with Python** by Jamie Flux: A step-by-step guide with code snippets for reservoir, production, well testing, and economics—explicitly designed for implementation and customization.
*   **Software Architecture with Python** by Anand Balachandran Pillai: Teaches how to design scalable, robust, and high-performance applications in Python—essential for structuring a multi-module suite.

### 🚀 Modern & Specialized Topics
To ensure your suite covers emerging demands from engineers.

*   **Modern Reservoir Engineering Handbook** by Sienna Newman: Connects classical fundamentals with **Python-assisted workflows**, history matching, unconventional analysis, uncertainty, and **CO₂ storage** evaluation.
*   **Estimating Developed Reserves in Unconventional Reservoirs** (SPEE Monograph 4): Essential for adding unconventional reserve evaluation and type-well analysis to your suite.
*   **Advanced Petroleum Reservoir Simulation: Towards Developing Reservoir Emulators** by M. Rafiqul Islam et al.: Covers emerging emulator and proxy modeling techniques.

### 💎 How to Prioritize
If you need to build in phases, a pragmatic sequence is:
1.  **Dake** for physics, plus **McCain** for fluids.
2.  **Lie’s MRST book** to build the simulator core, with **Peaceman** as the numerical reference.
3.  **Pyrcz’s free geostatistics e-book** to add the geological modeling front-end.
4.  **Ganat** for well testing, and **Guo** for production engineering.
5.  **Wheaton** or **Satter** for economics, and **Flux** or **Pillai** for the software architecture and Python implementation strategy.
6.  **Newman** and the **SPEE monograph** to extend into modern unconventional and CO₂ workflows.