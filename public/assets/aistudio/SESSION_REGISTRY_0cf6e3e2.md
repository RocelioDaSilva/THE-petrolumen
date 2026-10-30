# Architectural Design Document: Session Registry Pattern for State Isolation

**Status:** Proposed
**Author:** Jules (AI Software Engineer)
**Date:** October 2024
**Task:** T-2.1 — Session Registry Design Document
**Target Branch:** `jules/T-2.1-design-doc`

---

## 1. The Core Problem

During the concurrency audit documented in [`docs/audits/CONCURRENCY_REPRO.md`](../audits/CONCURRENCY_REPRO.md), state-bleed and state-pollution defects were confirmed across several core computation engines in PetroLúmen. These calculation engines are currently instantiated as **module-level global singletons**, causing all incoming HTTP requests—regardless of the authenticated user—to operate on and mutate the same in-memory object instances.

### Audit Findings Summary

1. **`res_simulator` (`ReservoirSimulator` / `FlowSimulation` in `backend/main.py`)**
   - **Defect:** Grid setup (`nx`, `dx`, `area`), fluid properties (`viscosity`, `compressibility`), rock properties (`permeability`, `porosity`), initial/boundary conditions, and well configurations overwrite each other in place on the shared `res_simulator` instance.
   - **Impact:** Concurrent user requests corrupt simulation setup. Executing `/run` reads mutated grid/pressure states, resulting in User A receiving simulation results computed from User B's grid and fluid parameters.

2. **`static_model_analyzer` (`StaticModeling` in `backend/gaia_genesis/api_v1/endpoints/static_modeling_tools.py`)**
   - **Defect:** Endpoints `/grid` and `/well-data` mutate shared dictionary attributes (`grid`, `well_data`) on the global `static_model_analyzer` instance.
   - **Impact:** Subsequent kriging, variogram, rock physics, or NMR operations execute against polluted grid dimensions and cross-contaminated well datasets from other users.

3. **`ai_predictor` (`AIPrediction` in `backend/main.py`)**
   - **Defect:** Training requests (`/train`) update instance properties (`feature_columns`, `best_model`, `models`, `scaler`).
   - **Impact:** When User A calls `/predict` after User B trains a model with a different set of feature columns, User A's request crashes with an HTTP 400/500 error (`Prediction data missing required feature columns`) due to overwritten feature schema.

4. **`dca_analyzer` (`DeclineAnalysis` in `backend/main.py`)**
   - **Status:** **Excluded from refactoring.** The audit verified that `dca_analyzer` methods (`fit_arps`, `forecast_production`, `calculate_eur`) are purely functional, stateless, and do not mutate instance state.

---

## 2. The Proposed Architecture: `SessionRegistry`

To achieve thread-safe and async-safe request isolation without requiring a complete rewrite of underlying calculation engine classes, PetroLúmen will introduce a user-scoped resource management system known as **`SessionRegistry`**.

### 2.1 Lifecycle and Lifespan Integration

The `SessionRegistry` instance will be initialized during FastAPI application startup via the `lifespan` context manager and attached to `app.state.session_registry`.

```python
# Conceptual App Lifespan Integration
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize SessionRegistry
    registry = SessionRegistry(
        default_ttl=settings.SESSION_TTL_SECONDS,  # e.g., 3600s (1 hour)
        max_capacity=settings.SESSION_MAX_ENTRIES   # e.g., 100 sessions
    )
    await registry.start_janitor_task()
    app.state.session_registry = registry
    logger.info("SessionRegistry initialized and Janitor cleanup task started.")

    yield

    # Shutdown: Clean up background tasks and release active sessions
    await registry.stop_janitor_task()
    await registry.clear_all()
    logger.info("SessionRegistry shut down successfully.")
```

### 2.2 Session Keying Scheme

Sessions will be keyed primarily by the authenticated user's unique ID (`user_id` from the JWT token). For workflows requiring multiple independent working contexts for a single user (e.g., side-by-side scenario modeling), an optional `X-Session-ID` header will be supported as a sub-key.

- **Primary Session Key Formula:** `session_key = f"{user_id}:{session_id}"` (or simply `str(user_id)` when no explicit session header is provided).

### 2.3 Session Store Data Structure

The registry maintains an in-memory mapping of session keys to scoped engine instances and metadata:

```python
class SessionContainer:
    def __init__(self, session_key: str):
        self.session_key: str = session_key
        self.created_at: float = time.time()
        self.last_accessed: float = time.time()
        self.engines: Dict[str, Any] = {}  # e.g. {"ai_predictor": AIPrediction(), ...}

    def touch(self) -> None:
        self.last_accessed = time.time()

    def is_expired(self, ttl_seconds: float) -> bool:
        return (time.time() - self.last_accessed) > ttl_seconds
```

### 2.4 Concurrency Safety

The `SessionRegistry` uses an `asyncio.Lock` to synchronize concurrent reads, instance creations, and background eviction sweeps across async request handlers:

```python
class SessionRegistry:
    def __init__(self, default_ttl: int = 3600, max_capacity: int = 100):
        self._sessions: Dict[str, SessionContainer] = {}
        self._lock = asyncio.Lock()
        self.default_ttl = default_ttl
        self.max_capacity = max_capacity
        self._janitor_task: Optional[asyncio.Task] = None

    async def get_or_create_engine(
        self, session_key: str, engine_type: str, factory_fn: Callable[[], Any]
    ) -> Any:
        async with self._lock:
            container = self._sessions.get(session_key)
            if container is None:
                # Capacity management: Evict LRU if at max capacity
                if len(self._sessions) >= self.max_capacity:
                    self._evict_lru_unlocked()

                container = SessionContainer(session_key)
                self._sessions[session_key] = container

            container.touch()
            if engine_type not in container.engines:
                container.engines[engine_type] = factory_fn()

            return container.engines[engine_type]
```

### 2.5 TTL Eviction & Memory Management (Janitor Task)

To prevent memory leaks from inactive client sessions holding large numerical arrays or trained models:
1. **Time-To-Live (TTL):** Inactive sessions where `now - last_accessed > SESSION_TTL_SECONDS` are purged automatically.
2. **Capacity Cap (LRU):** If total active sessions exceed `SESSION_MAX_ENTRIES`, the least-recently-accessed session is evicted immediately upon creation of a new session.
3. **Background Janitor Sweep:** A periodic async task executes every `SESSION_CLEANUP_INTERVAL_SECONDS` (e.g., every 300 seconds) to remove expired sessions.

```python
async def _janitor_loop(self) -> None:
    while True:
        try:
            await asyncio.sleep(settings.SESSION_CLEANUP_INTERVAL_SECONDS)
            async with self._lock:
                now = time.time()
                expired_keys = [
                    key for key, container in self._sessions.items()
                    if (now - container.last_accessed) > self.default_ttl
                ]
                for key in expired_keys:
                    del self._sessions[key]
                if expired_keys:
                    logger.info(f"Janitor purged {len(expired_keys)} expired sessions.")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in SessionRegistry janitor loop: {e}", exc_info=True)
```

---

## 3. Endpoint Migration Pattern

Endpoints will access computation engines using FastAPI's Dependency Injection (`Depends`). A dependency helper function will inspect the `USE_SESSION_REGISTRY` feature flag, retrieve the `SessionRegistry` from `app.state`, derive the session key from `current_user`, and return the session-scoped engine instance.

### 3.1 FastAPI Dependency Helper

```python
async def get_engine_instance(
    engine_name: str,
    factory_fn: Callable[[], Any],
    request: Request,
    current_user: UserResponse = Depends(get_current_active_user),
    session_id: Optional[str] = Header(None, alias="X-Session-ID"),
) -> Any:
    # Feature Flag Check for Backwards Compatibility
    if not settings.USE_SESSION_REGISTRY:
        # Fallback to legacy global singletons
        return get_legacy_global_singleton(engine_name)

    registry: SessionRegistry = request.app.state.session_registry
    session_key = f"{current_user.id}:{session_id}" if session_id else str(current_user.id)

    return await registry.get_or_create_engine(
        session_key=session_key,
        engine_type=engine_name,
        factory_fn=factory_fn,
    )
```

### 3.2 Endpoint Refactoring Pseudocode Comparison

#### Example A: AI Predictor (`/predict`)

**Before (Legacy Global Singleton):**
```python
# Legacy Implementation - UNSAFE
@app.post("/api/v1/reservoir/prediction/predict")
async def predict_with_ai_models(
    request: AIPredictRequest,
    current_user: UserResponse = Depends(get_current_active_user),
):
    if ai_predictor is None:
        raise HTTPException(status_code=503, detail="AIPrediction unavailable.")

    # Mutates and reads global singleton shared across all users
    if not all(col in df.columns for col in ai_predictor.feature_columns):
        raise HTTPException(status_code=400, detail="Feature mismatch.")

    predictions = ai_predictor.predict(df)
    return AIPredictResponse(predictions=predictions)
```

**After (Session Registry Scoped):**
```python
# Scoped Implementation - CONCURRENCY SAFE
def get_ai_predictor(
    request: Request,
    current_user: UserResponse = Depends(get_current_active_user),
) -> AIPrediction:
    return get_engine_instance(
        engine_name="ai_predictor",
        factory_fn=AIPrediction,
        request=request,
        current_user=current_user,
    )

@app.post("/api/v1/reservoir/prediction/predict")
async def predict_with_ai_models(
    request: AIPredictRequest,
    predictor: AIPrediction = Depends(get_ai_predictor),
    current_user: UserResponse = Depends(get_current_active_user),
):
    if not predictor.feature_columns:
        raise HTTPException(status_code=400, detail="Model not trained for this session.")

    predictions = predictor.predict(df)
    return AIPredictResponse(predictions=predictions)
```

#### Example B: Static Model Analyzer (`/grid`)

**Before (Legacy Global Singleton):**
```python
# Legacy Implementation - UNSAFE
@router.post("/grid")
async def create_3d_grid(request_data: GridRequest):
    # Directly mutates global module variable static_model_analyzer
    static_model_analyzer.create_3d_grid(...)
    return {"message": "3D Grid created successfully"}
```

**After (Session Registry Scoped):**
```python
# Scoped Implementation - CONCURRENCY SAFE
def get_static_analyzer(
    request: Request,
    current_user: UserResponse = Depends(get_current_active_user),
) -> StaticModeling:
    return get_engine_instance(
        engine_name="static_model_analyzer",
        factory_fn=StaticModeling,
        request=request,
        current_user=current_user,
    )

@router.post("/grid")
async def create_3d_grid(
    request_data: GridRequest,
    analyzer: StaticModeling = Depends(get_static_analyzer),
):
    analyzer.create_3d_grid(...)
    return {"message": "3D Grid created successfully"}
```

#### Example C: Reservoir Simulator (`/setup/grid` & Session Reset)

**Before (Legacy Global Singleton):**
```python
# Legacy Implementation - UNSAFE
@app.post("/api/v1/reservoir/flowsim/reset")
async def reset_flow_simulator():
    global res_simulator
    res_simulator = ReservoirSimulator(...) # Resets global instance for ALL users
```

**After (Session Registry Scoped):**
```python
# Scoped Implementation - CONCURRENCY SAFE
@app.post("/api/v1/reservoir/flowsim/reset")
async def reset_flow_simulator(
    request: Request,
    current_user: UserResponse = Depends(get_current_active_user),
    session_id: Optional[str] = Header(None, alias="X-Session-ID"),
):
    registry: SessionRegistry = request.app.state.session_registry
    session_key = f"{current_user.id}:{session_id}" if session_id else str(current_user.id)

    # Resets ONLY the requesting user's simulator instance
    await registry.reset_engine(session_key=session_key, engine_type="res_simulator")
    return {"message": "Session reservoir simulator reset successfully."}
```

---

## 4. Phased Migration Plan

To minimize risk and ensure thorough validation at each stage, refactoring will proceed in three sequential phases:

```
+-----------------------------------------------------------------------+
| Phase 1: ai_predictor                                                 |
| - Simplest state shape (models, feature_columns, best_model)          |
| - High urgency due to prediction crashes on feature mismatches        |
+-----------------------------------------------------------------------+
                                   │
                                   ▼
+-----------------------------------------------------------------------+
| Phase 2: static_model_analyzer                                        |
| - Moderate complexity (grid, well_data, variograms, nmr_data)         |
| - Refactor static_modeling_tools.py endpoints to use FastAPI Depends  |
+-----------------------------------------------------------------------+
                                   │
                                   ▼
+-----------------------------------------------------------------------+
| Phase 3: res_simulator                                                |
| - Highest complexity & statefulness (1D grid setup, fluid/rock, wells) |
| - Transition global /reset to session-scoped reset                    |
+-----------------------------------------------------------------------+
```

### Phase 1: `ai_predictor`
- **Scope:** Refactor `/api/v1/reservoir/prediction/train`, `/predict`, `/save-model`, and `/load-model`.
- **Rationale:** Lowest complexity, well-isolated state attributes (`models`, `feature_columns`, `best_model`). Refactoring this first validates the `SessionRegistry` infrastructure with minimal risk.
- **Verification:** Execute concurrent `/train` and `/predict` requests with different feature sets and verify zero cross-talk errors.

### Phase 2: `static_model_analyzer`
- **Scope:** Refactor all endpoints in `backend/gaia_genesis/api_v1/endpoints/static_modeling_tools.py` (`/grid`, `/well-data`, `/variogram`, `/kriging`, `/rock-physics`, `/nmr-data`).
- **Rationale:** Moderate complexity. Endpoints form a sequence of multi-step operations (`/grid` -> `/well-data` -> `/kriging`). Testing must ensure session continuity across endpoint calls for a single user.
- **Verification:** Execute concurrent spatial grid creation and kriging operations across two active sessions and verify isolated spatial datasets.

### Phase 3: `res_simulator`
- **Scope:** Refactor all endpoints in `/api/v1/reservoir/flowsim/*` (`/reset`, `/setup/*`, `/run`, `/well-rates`).
- **Rationale:** Highest statefulness and setup dependency chain. Refactoring replaces the global `/reset` with a user-scoped reset endpoint.
- **Verification:** Run concurrent 1D simulations with conflicting grid sizes and fluid viscosities, confirming each user receives accurate, unpolluted numerical results.

---

## 5. Backwards Compatibility & Feature Flag Strategy

To eliminate deployment risk and allow instant rollback if unexpected issues occur in production, the `SessionRegistry` pattern is guarded by a feature flag.

### 5.1 Configuration Setting

In `backend/config.py` (and environment variables):

```python
class Settings(BaseSettings):
    # Feature Flag for Session Registry Migration
    USE_SESSION_REGISTRY: bool = True

    # Session Registry Retention & Memory Management
    SESSION_TTL_SECONDS: int = 3600         # 1 Hour TTL
    SESSION_MAX_ENTRIES: int = 100          # Maximum concurrently cached sessions
    SESSION_CLEANUP_INTERVAL_SECONDS: int = 300  # Janitor sweep every 5 minutes
```

### 5.2 Dual-Path Fallback Behavior

When `USE_SESSION_REGISTRY` is set to `False`:
1. The dependency helper (`get_engine_instance`) bypasses `app.state.session_registry`.
2. It returns the existing global singletons (`ai_predictor`, `static_model_analyzer`, `res_simulator`).
3. Application behavior reverts exactly to the legacy implementation without requiring code changes or redeployments.

### 5.3 Rollback Plan

If production metrics indicate unanticipated memory growth or session degradation:
1. Set environment variable `USE_SESSION_REGISTRY=false`.
2. Restart application pods/containers.
3. The system instantly resumes operating on legacy singletons while diagnostics are gathered.

---

## 6. Summary of Deliverables & Exit Criterion

- **Deliverable:** Architectural design specification at `docs/design/SESSION_REGISTRY.md`.
- **Non-Deliverable:** No Python code changes in `backend/` or `main.py` under this task (T-2.1).
- **Exit Criterion:** Owner has reviewed and approved the architectural design for resolving the concurrency defects.
