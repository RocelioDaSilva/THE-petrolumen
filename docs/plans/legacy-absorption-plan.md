# Legacy Code Absorption & Elimination Plan

**Goal:** extract the remaining value from `legacy_archive/` (and the stray root
artifacts), merge it into the live project, then delete the legacy corpus.

**Status:** audit complete; first absorption slice (well-test analysis) done and
green. Deletion pending two decisions (see "Decision points" below).

---

## 1. What the audit found

The legacy corpus is ~59 MB / 767 files (712 git-tracked) plus a 1.3 GB
untracked "documents for competition…" folder that doubles as the install
source for the `ppes` package.

A symbol-level diff (AST) between legacy and the live backend shows the
**calculation algorithms are already absorbed**:

| Legacy source | Live equivalent (already in `backend/app/`) |
| :--- | :--- |
| `gaia_genesis/{production_analysis,forecasting,optimization,reserves_evaluation,history_matching}.py` | `engines/production/*` (0.94–0.96 similarity) |
| `gaia_genesis/{reservoir_analysis,reservoir_simulation,flow_simulation,compositional_modeling,advanced_simulation}.py` | `engines/reservoir/*` and `engines/reservoir/simulation/*` (0.95–0.97) |
| `gaia_genesis/{geomechanics,thermal_modeling,static_modeling}.py` | `engines/modeling/*` (0.93–0.98) |
| `gaia_genesis/{data_analytics,data_integration}.py` | `engines/analytics/*` (0.96) |
| `geology/mesh.py`, `analytics/ai_seismic.py`, `prediction/ai_prediction.py` | `engines/geology`, `engines/prediction` (0.92–1.00) |
| `reservoir_engineering/` package (80 files) | `engines/reservoir/reservoir_engineering.py` (MaterialBalance/WellTesting/DeclineAnalysis) |
| `flow_simulation/eclipse_simulator.py`, `tnavigator_python.py` | `engines/reservoir/simulation/commercial_simulator.py` (`CommercialSimulator`) |
| `mini oil and gas projects/` (13 Streamlit apps) | `backend/app/ui/*` + `backend/data/samples/legacy-engine-snapshot` |

The live backend has 349 top-level symbols vs 101 in the legacy flat engine
set, confirming the engines were migrated and extended.

## 2. Genuine gaps (worth absorbing)

1. **Well-test analysis** — Horner/MDH, Bourdet derivative, flow-regime
   detection, quality indicators. ✅ **DONE** (see §4).
2. **Grid/well/schedule data model** — legacy `ReservoirSimulator`
   (`create_structured_grid`, `create_corner_point_grid`, faults, wells,
   schedules, completions, well indices, import/export). Live
   `flow_simulation.py` has only `FlowSimulation`. → absorb as a modelling
   data structure, not its plot/import stubs.
3. **Typed API surface** — legacy `api_v1/endpoints/*` + `models/*` expose
   OGIP/STOIIP, EUR, FVF/Rs/viscosity/z, variogram/kriging, rock physics, NMR,
   static grid over engines that are already live. → port as stateless
   Pydantic wrappers (fix the stateful-global and auth-coupled design).
4. **Persistence layer** — `DatabaseManager`, `database_models.py`,
   `alembic/versions/*`, `User`, `ProductionData`, `WellPropertyData`,
   `DataUploader`. → *decision required* (see below).
5. **Auth** — `AuthManager`, JWT (`api/auth.py`). → *decision required*.

## 3. Elimination manifest (safe to delete once §2 is done)

| Path | Size | Reason |
| :--- | :--- | :--- |
| `legacy_archive/reservoir_engineering/` | 0.5 MB | algorithms absorbed; duplicate of `THE-petrolumen-cafa…` |
| `legacy_archive/THE-petrolumen-cafa… (2)/` | 1.0 MB | duplicate snapshot (28 duplicate groups detected) |
| `legacy_archive/petrolumen/` + `out/` | 3.3 MB | built Next.js artifacts, no source value |
| `legacy_archive/thepetrolumen/petrolumen/` (Next/Tauri frontend) | — | superseded by `src/` React app |
| `legacy_archive/thepetrolumen/thepetrolumen_new/possible feature calculation/` | — | third copy of `gaia_genesis` |
| `legacy_archive/thepetrolumen/thepetrolumen_new/backend/gaia_genesis/` | — | absorbed (see table) |
| `legacy_archive/mini oil and gas projects/` | 0.04 MB | absorbed into `backend/app/ui` + samples |
| `legacy_archive/*.zip`, `*.pdf`, `*.pptx` | 48 MB | marketing/build artifacts |
| root `project_tree.txt`, `project_tree_full.txt`, `TREE.txt`, `duplicate_report.txt`, `discovery.txt`, `dump_*.txt` | ~25 MB | generated scratch dumps |
| root `2025*Logotipo*.png` (30 files) | ~50 MB | logo iterations |

## 4. What was already done this session

- **New engine** `backend/app/engines/reservoir/well_test_analysis.py`:
  `bourdet_derivative`, `identify_flow_regimes`, `analyze_drawdown`,
  `analyze_buildup`, `horner_time` — stateless, field-unit-correct (net pay `h`,
  FVF `B`, and `initial_pressure`/`p_wf_at_shutin` now explicit; the legacy and
  first-absorbed versions dropped these terms).
- **New API** `backend/app/api/well_test_routes.py`:
  `POST /api/v1/reservoir/well-test/drawdown` and `/buildup` (typed
  request/response models, no auth dependency).
- **Tests** `backend/tests/test_well_test_analysis.py` (8 tests): synthetic
  line-source drawdown and Horner buildup recover permeability and skin
  exactly; derivative, validation, and edge-case coverage.

Result: `pytest backend/tests` = **132 passed, 1 pre-existing failure
(`/capabilities` schema), 8 skipped**.

## 5. Decision points (blocking the delete)

1. **Persistence + auth** — absorb the SQLAlchemy/Alembic models + JWT auth
   (needed for future multi-discipline projects) or leave the app stateless
   and discard them?
2. **`ppes` vendoring** — the live reservoir API imports `ppes`, which is
   installed editable from inside the 1.3 GB untracked folder. Before that
   folder can be deleted, `ppes` must be vendored under `backend/vendor/` or
   pinned as a real dependency.
3. **History rewrite** — `git rm` shrinks the working tree only; `git
   filter-repo` is required to actually reclaim the ~1.6 GB `.git`. Run it?
