# Python engine merge plan

## Scope and path roots

Use the comparison inventory in [engines-comparison.md](./engines-comparison.md). This checklist includes only Variant B and A-main; **A-embedded-copy is intentionally excluded**.

- **A-main:** `thepetrolumen/thepetrolumen_new/backend/gaia_genesis/`
- **B:** `THE-petrolumen-cafa105c2124580e244b9abca798a163d4588449 (2)/THE-petrolumen-cafa105c2124580e244b9abca798a163d4588449/gaia_genesis/`
- **Canonical engine root:** `backend/app/engines/`

`PORT_NEW` destinations below are proposed as `backend/app/engines/<source-relative-path>`; confirm package layout and imports before porting. The inventory compares paths and Python declarations, not engineering behavior, dependency compatibility, or runtime correctness.

## `PORT_NEW` — add as new modules

These source-relative paths have no canonical module with the same basename. Paths under **Both** occur in A-main and B; review those two snapshots before choosing or combining their implementations.

### Both A-main and B (22)

- [ ] `analytics/advanced_analytics.py`
- [ ] `analytics/ai_seismic.py`
- [ ] `data_analytics.py`
- [ ] `data_integration.py`
- [ ] `flow_history_matching.py`
- [ ] `flow_simulation.py`
- [ ] `geology/mesh.py`
- [ ] `geomechanics.py`
- [ ] `history_matching.py`
- [ ] `production_analysis.py`
- [ ] `production_forecasting.py`
- [ ] `production_optimization.py`
- [ ] `reserves_evaluation.py`
- [ ] `reservoir_analysis.py`
- [ ] `reservoir_engineering.py`
- [ ] `reservoir_simulation.py`
- [ ] `simulator_integration.py`
- [ ] `static_modeling.py`
- [ ] `thermal_modeling.py`
- [ ] `uncertainty_analysis.py`
- [ ] `well_models.py`
- [ ] `workflow_automation.py`

### A-main only (1)

- [ ] `prediction/ai_prediction.py`

### B only (38)

- [ ] `geology/digital_rock.py`
- [ ] `geology/geostatistics.py`
- [ ] `geology/model3d.py`
- [ ] `geology/nmr_analysis.py`
- [ ] `geology/petrophysics.py`
- [ ] `geology/reservoir_characterization.py`
- [ ] `geology/seismic_integration.py`
- [ ] `geology/sensitivity.py`
- [ ] `pvt/correlations.py`
- [ ] `pvt/dca.py`
- [ ] `pvt/eos_solver.py`
- [ ] `pvt/mbal.py`
- [ ] `pvt/z_factor.py`
- [ ] `reservoir_engineering/api/auth.py`
- [ ] `reservoir_engineering/data_management/data_uploader.py`
- [ ] `reservoir_engineering/database/db_manager.py`
- [ ] `reservoir_engineering/decline_analysis/decline_analysis.py`
- [ ] `reservoir_engineering/economics/economic_analysis.py`
- [ ] `reservoir_engineering/flow_simulation/eclipse_simulator.py`
- [ ] `reservoir_engineering/flow_simulation/flow_simulator.py`
- [ ] `reservoir_engineering/flow_simulation/reservoir_simulator.py`
- [ ] `reservoir_engineering/flow_simulation/tnavigator_python.py`
- [ ] `reservoir_engineering/geological_integration/geological_data.py`
- [ ] `reservoir_engineering/geostatistics/geostatistics.py`
- [ ] `reservoir_engineering/history_matching/history_matching.py`
- [ ] `reservoir_engineering/prediction/ai_prediction.py`
- [ ] `reservoir_engineering/pvt/pvt_properties.py`
- [ ] `reservoir_engineering/simulation/compositional_simulation.py`
- [ ] `reservoir_engineering/simulation/reservoir_simulation.py`
- [ ] `reservoir_engineering/simulation/thermal_simulation.py`
- [ ] `reservoir_engineering/static_modeling/static_model.py`
- [ ] `reservoir_engineering/tests/test_prediction.py`
- [ ] `reservoir_engineering/visualization/reservoir_visualization.py`
- [ ] `reservoir_engineering/well_testing/well_test.py`
- [ ] `reservoir_engineering/well_testing/well_testing.py`
- [ ] `visualization/advanced_visualization.py`
- [ ] `visualization/results_visualizer.py`
- [ ] `visualization/visualizer3d.py`

## `REVIEW_DIFF` — compare manually; do not overwrite

The source paths below share a basename with a canonical module at a different path. Class, method, and body observations are AST-level triage; they are not a substitute for checking imports, constants, numerical logic, tests, and runtime behavior.

| Source path(s) | Canonical path | Major class/function comparison |
|---|---|---|
| A-main `advanced_simulation.py`; B `advanced_simulation.py` | `backend/app/engines/reservoir/simulation/advanced_simulation.py` | `AdvancedSimulation` is declared in both. A-main method bodies differ for `__init__`, `apply_advanced_well_model`, `calculate_matrix_fracture_transfer`, `calculate_uncertainty_analysis`, `enable_dual_porosity`, `enable_geomechanical_coupling`, `run_timestep`, and `update_thermal_properties`; B's method bodies match the canonical AST. |
| A-main `compositional_modeling.py`; B `compositional_modeling.py` | `backend/app/engines/reservoir/simulation/compositional_modeling.py` | Same declared classes (`Component`, `EquationOfState`, `PengRobinsonEOS`, `FlashCalculation`, `CompositionalModel`). A-main method bodies differ in `Component.__init__`, `CompositionalModel.__init__`, `CompositionalModel.calculate_phase_properties`, `CompositionalModel.perform_flash`, `EquationOfState.__init__`, `EquationOfState.calculate_fugacity_coefficients`, `EquationOfState.calculate_phase_densities`, `EquationOfState.calculate_z_factor`, `FlashCalculation.__init__`, `FlashCalculation._rachford_rice`, `FlashCalculation.perform_flash`, `PengRobinsonEOS._calculate_mixture_parameters`, `PengRobinsonEOS.calculate_fugacity_coefficients`, and `PengRobinsonEOS.calculate_z_factor`; B's method bodies match the canonical AST. |
| B `commercial_simulator.py` | `backend/app/engines/reservoir/simulation/commercial_simulator.py` | `CommercialSimulator`; no declared API or method-body delta found by AST comparison. Check module-level imports, configuration, and dependencies. |
| B `reservoir_engineering/history_matching/history_matcher.py` | `backend/app/engines/reservoir/simulation/history_matcher.py` | `HistoryMatcher` has a substantially different API. B provides `define_parameters`, `set_historical_data`, `analyze_uncertainty`, `export_results`, and `visualize_results`; canonical provides `add_parameter`, `add_constraint`, `build_proxy_model`, and `calculate_misfit`. `__init__` and `run_matching` signatures also differ. B's `run_matching` accepts a simulator and method (default `Nelder-Mead`); canonical takes an algorithm (default `gradient`) and is initialized with a simulator controller and observed data. |
| B `simulation/auto_diff.py` | `backend/app/engines/reservoir/simulation/auto_diff.py` | `Variable` and `AutoDiff`; no declared API or method-body delta found by AST comparison. |
| B `simulation/black_oil_simulator.py` | `backend/app/engines/reservoir/simulation/black_oil_simulator.py` | `BlackOilSimulator`; no declared API or method-body delta found by AST comparison. |
| B `simulation/compositional_simulator.py` | `backend/app/engines/reservoir/simulation/compositional_simulator.py` | `CompositionalSimulator`; no declared API or method-body delta found by AST comparison. |
| B `simulation/eor_simulator.py` | `backend/app/engines/reservoir/simulation/eor_simulator.py` | `EORSimulator`; no declared API or method-body delta found by AST comparison. |
| B `simulation/history_matcher.py` | `backend/app/engines/reservoir/simulation/history_matcher.py` | `HistoryMatcher`; no declared API or method-body delta found by AST comparison. This and B's nested `reservoir_engineering/history_matching/history_matcher.py` both target the same canonical module, so reconcile them together rather than applying either as a replacement. |
| B `simulation/network_designer.py` | `backend/app/engines/reservoir/simulation/network_designer.py` | `NetworkElement`, `Well`, `Separator`, `Pipeline`, and `NetworkDesigner`; no declared API or method-body delta found by AST comparison. |
| B `simulation/parallel_engine.py` | `backend/app/engines/reservoir/simulation/parallel_engine.py` | `ParallelEngine`; no declared API or method-body delta found by AST comparison. |
| B `simulation/production_optimizer.py` | `backend/app/engines/reservoir/simulation/production_optimizer.py` | `ProductionOptimizer`; no declared API or method-body delta found by AST comparison. |
| B `simulation/proxy_models.py` | `backend/app/engines/reservoir/simulation/proxy_models.py` | `ReservoirProxy`, `WellProductionProxy`, `PressureProxy`, and `SaturationProxy`; no declared API or method-body delta found by AST comparison. |
| B `simulation/simulation_controller.py` | `backend/app/engines/reservoir/simulation/simulation_controller.py` | `SimulationController`; no declared API or method-body delta found by AST comparison. |
| B `simulation/thermal_simulator.py` | `backend/app/engines/reservoir/simulation/thermal_simulator.py` | `ThermalSimulator`; no declared API or method-body delta found by AST comparison. |

## `IGNORE` — out of scope for this engine merge

- [ ] Ignore all `__init__.py` files, including package export lists; map any needed exports deliberately in a separate package-integration task.
- [ ] Ignore all `api_v1/` files.
- [ ] Ignore all `core/` files.
- [ ] Ignore root `main.py`.

## Merge order

- [ ] Port `PORT_NEW` modules only after checking their imports, package dependencies, and applicable tests.
- [ ] Resolve every `REVIEW_DIFF` pair before changing canonical files; specifically reconcile the two B history-matcher candidates that map to one canonical path.
- [ ] Keep all `IGNORE` items out of this change.
