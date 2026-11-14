# API Reference

This reference covers the operations registered by `backend/app/main.py` and
exposed in the FastAPI OpenAPI schema. It lists the request and response
Pydantic models by their source names. `—` means there is no request body.

The application also serves `GET /`, which redirects to `/docs`; it is
intentionally excluded from OpenAPI. Unless noted otherwise, request validation
errors return HTTP 422. Calculation input errors commonly return 400 or 422;
consult the route implementation for individual error cases.

## Simulation

| Method | Endpoint | Request schema | Response schema | Purpose / notes |
|---|---|---|---|---|
| POST | `/api/simulate/black-oil` | `BlackOilInput` (`GridInput`, `WellInput`) | `BlackOilResponse` | Simplified pressure and saturation simulation; maximum 512 grid cells. See [engine limitations](ENGINE_CAPABILITIES.md#black-oil-simulation). |
| POST | `/api/simulate/compositional` | `CompositionalInput` (`GridInput`, `ComponentInput`) | HTTP 501 (`UnimplementedResponse` shape) | Reserved endpoint; compositional flow solver is not implemented. |
| POST | `/api/simulate/thermal` | `ThermalInput` (`CompositionalInput`, `ThermalPropertiesInput`) | HTTP 501 (`UnimplementedResponse` shape) | Reserved endpoint; thermal flow and heat-transfer solver are not implemented. |

The two unimplemented routes have no declared success response model. Their
HTTP 501 body wraps the `detail` and `tracking` fields under the error's
`detail` key.

## General engineering calculations

| Method | Endpoint | Request schema | Response schema | Purpose / notes |
|---|---|---|---|---|
| POST | `/api/engine/pvt/eos` | `EosRequest` (`EosComponentInput`) | `EosResponse` | PR or SRK mixture vapor-root Z-factor. Pressure is Pa and temperature is K. |
| POST | `/api/engine/pvt/flash` | `FlashRequest` (`EosComponentInput`) | `FlashResponse` | Isothermal Wilson-K / Rachford-Rice phase split; not fugacity-iterated equilibrium. |
| POST | `/api/engine/drilling/trajectory` | `SurveyInput` | `TrajectoryResponse` | Minimum-curvature directional survey coordinates. |
| POST | `/api/engine/geology/grid` | `GridRequest` | `GridResponse` | Cartesian grid dimensions, cell count, and bulk volume; supports per-cell spacing. |
| POST | `/api/engine/reservoir/nodal` | `NodalRequest` | `NodalResponse` | Finds the rate at a simplified Vogel IPR / TPR intersection. |
| POST | `/api/engine/reservoir/compressibility/rock` | `RockCompressibilityRequest` | `RockCompressibilityResponse` | Newman's sandstone or limestone pore-volume compressibility with range reporting and optional strict range enforcement. |
| POST | `/api/engine/reservoir/compressibility/gas` | `GasCompressibilityRequest` | `GasCompressibilityResponse` | Gas isothermal compressibility and Z derivative from Hall-Yarborough with Sutton pseudocritical properties. |
| POST | `/api/engine/reservoir/compressibility/total` | `TotalCompressibilityRequest` | `TotalCompressibilityResponse` | Phase-weighted total compressibility using gas, user-supplied oil/water values, and rock compressibility. |

## Reservoir capability, IPR, and decline routes

| Method | Endpoint | Request schema | Response schema | Purpose / notes |
|---|---|---|---|---|
| GET | `/api/v1/reservoir/capabilities` | — | `ReservoirCapabilitiesResponse` | Lists selected PVT, IPR, decline, and compressibility capabilities and their stated scope. |
| POST | `/api/v1/reservoir/vogel` | `VogelRequest` | `VogelResponse` | Vogel IPR rate for a two-phase oil reservoir. |
| POST | `/api/v1/reservoir/vogel/curve` | `VogelCurveRequest` | `VogelCurveResponse` | Batch inverse Vogel IPR curve (rate to flowing pressure). |
| POST | `/api/v1/reservoir/z-factor` | `ZFactorRequest` | `ZFactorResponse` | Hall-Yarborough gas Z-factor using Sutton pseudocritical properties. Inputs use psia, °F, and gas specific gravity. |
| POST | `/api/v1/reservoir/decline/exponential` | `ExponentialDeclineRequest` | `ExponentialDeclineResponse` | Exponential decline rate and cumulative production. Time units must match the decline-rate units. |
| GET | `/api/v1/reservoir/health` | — | `ReservoirHealthResponse` | Health/status check for the ppes reservoir module. |

## Reservoir black-oil PVT routes

These six routes use `backend/app/engines/reservoir/black_oil_pvt.py`; responses
include correlation names and validity-range indicators where applicable.

| Method | Endpoint | Request schema | Response schema | Purpose / notes |
|---|---|---|---|---|
| POST | `/api/engine/reservoir/pvt/gas-viscosity` | `GasViscosityRequest` | `GasViscosityResponse` | Lee-Gonzalez-Eakin gas viscosity, density, and intermediate factors. Supply exactly one of gas specific gravity or molecular weight. |
| POST | `/api/engine/reservoir/pvt/oil-rso` | `OilRequest` | `OilRsoResponse` | Standing/Beggs solution gas-oil ratio. |
| POST | `/api/engine/reservoir/pvt/oil-bo` | `OilBoRequest` | `OilBoResponse` | Standing/Beggs oil formation-volume factor; optional oil compressibility correction input. |
| POST | `/api/engine/reservoir/pvt/oil-compressibility` | `OilRequest` | `OilCompressibilityResponse` | Villena-Lanzi or Vasquez-Beggs oil compressibility. |
| POST | `/api/engine/reservoir/pvt/oil-viscosity` | `OilRequest` | `OilViscosityResponse` | Egbogah / Beggs-Robinson / Vasquez-Beggs oil viscosity. |
| POST | `/api/engine/reservoir/pvt/water` | `WaterPVTRequest` | `WaterPVTResponse` | McCain/Osif formation-water FVF, solution gas, compressibility, and viscosity. |

## Chapter 2 PVT correlations

These `/api/v1/reservoir/pvt/*` calculations use the ppes bridge and field
units identified in each request model. Calculation responses are
`CalculationResponse` dictionaries (`dict[str, float | str]`).

| Method | Endpoint | Request schema | Response schema | Purpose |
|---|---|---|---|---|
| GET | `/api/v1/reservoir/capabilities/pvt` | — | `ReservoirPvtCapabilityResponse` | Lists Chapter 2 PVT calculations. |
| GET | `/api/v1/reservoir/health/pvt` | — | `ReservoirPvtHealthResponse` | PVT module health/status. |
| POST | `/api/v1/reservoir/pvt/rs-standing` | `RsRequest` | `CalculationResponse` | Standing solution gas-oil ratio. |
| POST | `/api/v1/reservoir/pvt/bo-standing` | `BoRequest` | `CalculationResponse` | Standing oil formation-volume factor. |
| POST | `/api/v1/reservoir/pvt/mu-dead-oil` | `MuDeadRequest` | `CalculationResponse` | Dead-oil viscosity. |
| POST | `/api/v1/reservoir/pvt/mu-sat-oil` | `MuSatRequest` | `CalculationResponse` | Saturated-oil viscosity. |
| POST | `/api/v1/reservoir/pvt/mu-unsat-oil` | `MuUnsatRequest` | `CalculationResponse` | Undersaturated-oil viscosity. |
| POST | `/api/v1/reservoir/pvt/mu-gas-low-pressure` | `MuGasRequest` | `CalculationResponse` | Low-pressure gas viscosity with optional sour-gas fractions. |
| POST | `/api/v1/reservoir/pvt/rho-oil` | `RhoOilRequest` | `CalculationResponse` | Live-oil density. |
| POST | `/api/v1/reservoir/pvt/rho-gas` | `RhoGasRequest` | `CalculationResponse` | Gas density. |
| POST | `/api/v1/reservoir/pvt/bg` | `BgRequest` | `CalculationResponse` | Gas formation-volume factor. |
| POST | `/api/v1/reservoir/pvt/eg` | `BgRequest` | `CalculationResponse` | Gas expansion factor (inverse of `Bg`). |
| POST | `/api/v1/reservoir/pvt/oil-compressibility` | `CoRequest` | `CalculationResponse` | Oil compressibility. |
| POST | `/api/v1/reservoir/pvt/wichert-aziz` | `WazRequest` | `CalculationResponse` | Sour-gas pseudocritical correction. |
| POST | `/api/v1/reservoir/pvt/z-brill-beggs` | `ZBrillRequest` | `CalculationResponse` | Brill-Beggs Z-factor with pseudocritical properties from gas gravity. |

## Choke, tubing, and gas-lift calculations

These routes are based on the ppes Chapter 5, 9, and 13 bridge. Scalar
calculation responses use `CalculationResponse` (`dict[str, float | str]`).

| Method | Endpoint | Request schema | Response schema | Purpose |
|---|---|---|---|---|
| GET | `/api/v1/reservoir/capabilities/ch5-9-13` | — | `ReservoirChaptersCapabilityResponse` | Lists available choke, tubing, and gas-lift calculations. |
| GET | `/api/v1/reservoir/health/ch5-9-13` | — | `ReservoirChaptersHealthResponse` | Health/status for Chapters 5, 9, and 13. |
| POST | `/api/v1/reservoir/choke/gilbert` | `GilbertRequest` | `CalculationResponse` | Gilbert wellhead choke pressure correlation. |
| POST | `/api/v1/reservoir/choke/critical-ratio` | `CriticalRatioRequest` | `CalculationResponse` | Critical gas pressure ratio. |
| POST | `/api/v1/reservoir/choke/sonic-gas` | `SonicGasRequest` | `CalculationResponse` | Critical/sonic gas flow through a choke. |
| POST | `/api/v1/reservoir/choke/subsonic-gas` | `SubsonicGasRequest` | `CalculationResponse` | Subcritical gas flow through a choke. |
| POST | `/api/v1/reservoir/tubing/collapse-biaxial` | `CollapseBiaxialRequest` | `CalculationResponse` | Biaxial-corrected tubing collapse pressure. |
| POST | `/api/v1/reservoir/tubing/ballooning` | `BallooningRequest` | `CalculationResponse` | Tubing length change from pressure-induced ballooning. |
| POST | `/api/v1/reservoir/tubing/piston` | `PistonRequest` | `CalculationResponse` | Piston-effect force and/or tubing length change. |
| POST | `/api/v1/reservoir/tubing/bending-stress` | `BendingRequest` | `CalculationResponse` | Bending stress in a curved tubing string. |
| POST | `/api/v1/reservoir/gas-lift/valve-depth` | `ValveDepthRequest` | `CalculationResponse` | Depth of the first unloading valve. |
| POST | `/api/v1/reservoir/gas-lift/valve-open-close` | `ValvePressuresRequest` | `CalculationResponse` | Gas-lift valve opening and closing pressures. |
| POST | `/api/v1/reservoir/gas-lift/orifice-size` | `OrificeRequest` | `CalculationResponse` | Orifice area and diameter for a target injection rate. |
| POST | `/api/v1/reservoir/gas-lift/injection-glr` | `InjectionGlrRequest` | `CalculationResponse` | Required injection gas-liquid ratio. |

## Material balance and well testing

| Method | Endpoint | Request schema | Response schema | Purpose / notes |
|---|---|---|---|---|
| POST | `/api/engine/pvt/mbal` | `MbalRequest` (`ProductionPointInput`, `PvtPointInput`) | `MbalResponse` | Havlena-Odeh oil or gas material-balance scalar estimate. If `pvt_data` is omitted, built-in default points are used; drive indices are not calculated and the response reports `null`. |
| POST | `/api/v1/reservoir/well-test/drawdown` | `DrawdownRequest` | `DrawdownResponse` (`FlowRegimesResponse`) | Semilog drawdown analysis and heuristic flow-regime diagnostics. |
| POST | `/api/v1/reservoir/well-test/buildup` | `BuildupRequest` | `BuildupResponse` (`FlowRegimesResponse`) | Horner buildup analysis and heuristic flow-regime diagnostics. |

## Charts

All chart responses use `ChartResponse`, containing a base64-encoded PNG in
`image_base64` and its `content_type`.

| Method | Endpoint | Request schema | Response schema | Purpose |
|---|---|---|---|---|
| POST | `/api/engine/geology/grid/chart` | `GridRequest` | `ChartResponse` | Render grid extents and bulk volume. |
| POST | `/api/engine/pvt/eos/chart` | `EosRequest` | `ChartResponse` | Plot Z-factor across a pressure sweep around the requested state. |
| POST | `/api/engine/reservoir/nodal/chart` | `NodalRequest` | `ChartResponse` | Plot IPR and TPR curves and their operating point. |
| POST | `/api/engine/drilling/trajectory/chart` | `SurveyInput` | `ChartResponse` | Render plan and side views of the minimum-curvature trajectory. |

## Production and petrophysics

| Method | Endpoint | Request schema | Response schema | Purpose / notes |
|---|---|---|---|---|
| POST | `/api/engine/production/economics` | `ProductionEconomicsRequest` | `ProductionEconomicsResponse` (`CashFlowDetails`) | Annual oil/gas/water economic evaluation, cash-flow details, NPV, IRR, payout, and ROI. |
| POST | `/api/production/import/csv` | Multipart `file` (`.csv`) | `ProductionCsvImportResponse` | Authenticated import of production history; 10 MB and 50,000 data-row limits. |
| GET | `/api/production/wells` | — | `list[ProductionWellResponse]` | Lists only wells owned by the authenticated user. Requires Bearer token. |
| GET | `/api/production/overview` | — | `ProductionOverviewResponse` (`ProductionTrendPoint`, `ProductionWellLatestResponse`) | User-scoped production-rate time series, latest per-well rates, and latest import time. Requires Bearer token. |
| POST | `/api/petrophysics/las/parse` | Multipart `file` (`.las`) | `LasParseResponse` (`CurveStats`) | Parses LAS metadata and returns curve names, sample count, depth range, and per-curve statistics. |
| POST | `/api/engine/petrophysics/facies/classify` | `FaciesClassifyRequest` (`FaciesLogRecord`, `LabeledFaciesLogRecord`) | `FaciesClassifyResponse` | Random Forest facies classification; default training data contains only eight inline benchmark samples. |
| POST | `/api/workflow/ooip/upload` | Multipart `file` (`.las`) | `OoipUploadResponse` | Parses LAS curves into a temporary in-memory session. Upload limit is 10 MiB; sessions expire after one hour and are process-local. |
| POST | `/api/workflow/ooip/run` | `OoipRunRequest` (`ArchieParams`) | `OoipRunResponse` | Archie-based volumetric OOIP estimate over the uploaded session curves. |

## Authentication and saved simulations

Register, login, and saved-run routes are defined in
`backend/app/persistence/routes.py`. Saved records and production data are
scoped to the authenticated owner. Authenticated endpoints require
`Authorization: Bearer <access_token>`.

| Method | Endpoint | Request schema | Response schema | Purpose / notes |
|---|---|---|---|---|
| POST | `/api/auth/register` | `UserCreate` | `UserOut` (201) | Register a user; duplicate username/email returns 409. |
| POST | `/api/auth/token` | `UserLogin` | `Token` | Issue a bearer token. |
| GET | `/api/auth/me` | — | `UserOut` | Return the authenticated user's profile. |
| POST | `/api/saved-simulations` | `SavedSimulationCreate` | `SavedSimulationOut` (201) | Save JSON-safe simulation inputs/results for the authenticated user. |
| GET | `/api/saved-simulations` | Query: `limit`, `offset` | `list[SavedSimulationSummary]` | List the authenticated user's saved runs; default limit 50, maximum 100. |
| GET | `/api/saved-simulations/{simulation_id}` | Path: `simulation_id` | `SavedSimulationOut` | Fetch one owned saved run; inaccessible or missing records return 404. |
| DELETE | `/api/saved-simulations/{simulation_id}` | Path: `simulation_id` | Empty (204) | Delete one owned saved run; inaccessible or missing records return 404. |

## Health

| Method | Endpoint | Request schema | Response schema | Purpose |
|---|---|---|---|---|
| GET | `/health` | — | `HealthResponse` | Application health and API version. |
