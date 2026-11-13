/**
 * Typed HTTP client for the ppes-backed reservoir API.
 */
export function resolveApiBaseUrl(search: string, configuredUrl?: string): string {
  const configuredBaseUrl = configuredUrl?.replace(/\/+$/, '');
  if (configuredBaseUrl) return configuredBaseUrl;

  const apiPort = new URLSearchParams(search).get('api_port');
  if (apiPort && /^\d+$/.test(apiPort)) {
    const port = Number(apiPort);
    if (port > 0 && port <= 65535) return `http://127.0.0.1:${port}`;
  }
  return 'http://localhost:8000';
}

const BASE_URL: string = resolveApiBaseUrl(
  typeof window === 'undefined' ? '' : window.location.search,
  import.meta.env.VITE_API_URL as string | undefined,
);

export type ApiError = { status: number; detail: string };
let apiAuthToken: string | null = null;

export function setApiAuthToken(token: string | null): void {
  apiAuthToken = token;
}

export function getApiAuthToken(): string | null {
  return apiAuthToken;
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`;
  let res: Response;
  try {
    const headers = new Headers(init?.headers);
    if (
      !headers.has('Content-Type') &&
      !(typeof FormData !== 'undefined' && init?.body instanceof FormData)
    ) {
      headers.set('Content-Type', 'application/json');
    }
    if (apiAuthToken) headers.set('Authorization', `Bearer ${apiAuthToken}`);
    res = await fetch(url, {
      ...init,
      headers,
    });
  } catch (e) {
    throw { status: 0, detail: `Network error reaching ${url}: ${(e as Error).message}` } satisfies ApiError;
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body?.detail === 'string'
        ? body.detail
        : JSON.stringify(body?.detail ?? body);
    } catch { /* keep statusText */ }
    throw { status: res.status, detail } satisfies ApiError;
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export interface AuthUser {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
}

interface AuthTokenResponse {
  access_token: string;
  token_type: 'bearer';
}

export interface SavedSimulationSummary {
  id: number;
  name: string;
  simulation_type: string;
  created_at: string;
}

export interface SavedSimulation extends SavedSimulationSummary {
  input_data: Record<string, unknown>;
  result_data: Record<string, unknown>;
}

export function registerAccount(input: {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}): Promise<AuthUser> {
  return call<AuthUser>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export function requestAuthToken(input: {
  username: string;
  password: string;
}): Promise<AuthTokenResponse> {
  return call<AuthTokenResponse>('/api/auth/token', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export function fetchCurrentUser(): Promise<AuthUser> {
  return call<AuthUser>('/api/auth/me');
}

export function createSavedSimulation(input: {
  name: string;
  simulation_type: string;
  input_data: Record<string, unknown>;
  result_data: Record<string, unknown>;
}): Promise<SavedSimulation> {
  return call<SavedSimulation>('/api/saved-simulations', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export function fetchSavedSimulations(
  limit = 50,
  offset = 0,
): Promise<SavedSimulationSummary[]> {
  return call<SavedSimulationSummary[]>(
    `/api/saved-simulations?limit=${limit}&offset=${offset}`,
  );
}

export function fetchSavedSimulation(id: number): Promise<SavedSimulation> {
  return call<SavedSimulation>(`/api/saved-simulations/${id}`);
}

export function removeSavedSimulation(id: number): Promise<void> {
  return call<void>(`/api/saved-simulations/${id}`, { method: 'DELETE' });
}

export interface ProductionCsvImportResponse {
  rows_received: number;
  rows_imported: number;
  rows_skipped_duplicates: number;
  wells_created: number;
}

export interface ProductionWell {
  id: number;
  name: string;
  field: string | null;
  latitude: number | null;
  longitude: number | null;
}

export interface ProductionTrendPoint {
  date: string;
  oil_rate: number;
  gas_rate: number;
  water_rate: number;
}

export interface ProductionWellLatestRates {
  well_id: number;
  well_name: string;
  date: string;
  oil_rate: number | null;
  gas_rate: number | null;
  water_rate: number | null;
}

export interface ProductionOverview {
  series: ProductionTrendPoint[];
  latest_import_at: string | null;
  latest_well_rates: ProductionWellLatestRates[];
}

export function fetchProductionWells(): Promise<ProductionWell[]> {
  return call<ProductionWell[]>('/api/production/wells');
}

export function fetchProductionOverview(): Promise<ProductionOverview> {
  return call<ProductionOverview>('/api/production/overview');
}

export function importProductionCsv(file: File): Promise<ProductionCsvImportResponse> {
  const formData = new FormData();
  formData.append('file', file);
  return call<ProductionCsvImportResponse>('/api/production/import/csv', {
    method: 'POST',
    body: formData,
  });
}

export type RockType = 'sandstone' | 'limestone';

export interface RockCompressibilityRequest {
  phi: number;
  rock_type: RockType;
  strict: boolean;
}

export interface RockCompressibilityResponse {
  cf_psi_inv: number;
  rock_type: RockType;
  in_validity_range: boolean;
}

export interface GasCompressibilityRequest {
  p_psia: number;
  temperature_f: number;
  gas_sg: number;
  h_psi?: number;
}

export interface GasCompressibilityResponse {
  cg_psi_inv: number;
  z_at_p: number;
  dz_dp_psi_inv: number;
  h_psi: number;
  method: 'central' | 'forward';
  z_correlation: string;
}

export interface TotalCompressibilityRequest extends GasCompressibilityRequest {
  phi: number;
  rock_type: RockType;
  strict_rock_range: boolean;
  co_psi_inv: number;
  cw_psi_inv: number;
  sg: number;
  so: number;
  sw: number;
}

export interface TotalCompressibilityResponse {
  ct_psi_inv: number;
  cg_psi_inv: number;
  cf_psi_inv: number;
  z_at_p: number;
  dz_dp_psi_inv: number;
  in_rock_validity_range: boolean;
  z_correlation: string;
}

export function calculateRockCompressibility(
  input: RockCompressibilityRequest,
): Promise<RockCompressibilityResponse> {
  return call('/api/engine/reservoir/compressibility/rock', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export function calculateGasCompressibility(
  input: GasCompressibilityRequest,
): Promise<GasCompressibilityResponse> {
  return call('/api/engine/reservoir/compressibility/gas', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export function calculateTotalCompressibility(
  input: TotalCompressibilityRequest,
): Promise<TotalCompressibilityResponse> {
  return call('/api/engine/reservoir/compressibility/total', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export function healthReservoir() {
  return call<{ status: string; module: string; engine: string }>('/api/v1/reservoir/health');
}

export type VogelInput = { qmax: number; pwf: number; pbar: number };
export type VogelResponse = { q: number; method: string };
export function vogel(input: VogelInput) {
  return call<VogelResponse>('/api/v1/reservoir/vogel', { method: 'POST', body: JSON.stringify(input) });
}

export type VogelCurvePoint = { q: number; pwf: number };
export type VogelCurveResponse = { points: VogelCurvePoint[]; method: string };
export function vogelCurve(input: { qmax: number; pbar: number; n_points?: number }) {
  return call<VogelCurveResponse>('/api/v1/reservoir/vogel/curve', {
    method: 'POST',
    body: JSON.stringify({ n_points: 25, ...input }),
  });
}

export type ZFactorInput = { p: number; t_F: number; gamma_g: number };
export type ZFactorResponse = { z: number; p_pr: number; t_pr: number; p_pc: number; t_pc: number; method: string };
export function zFactor(input: ZFactorInput) {
  return call<ZFactorResponse>('/api/v1/reservoir/z-factor', { method: 'POST', body: JSON.stringify(input) });
}

export type ExponentialDeclineInput = { qi: number; b: number; t: number };
export type ExponentialDeclineResponse = { q: number; cumulative: number; method: string };
export function exponentialDecline(input: ExponentialDeclineInput) {
  return call<ExponentialDeclineResponse>('/api/v1/reservoir/decline/exponential', { method: 'POST', body: JSON.stringify(input) });
}

export type GilbertInput = { q_bpd: number; glr: number; choke_64: number };
export type GilbertResponse = { p_wh: number; method: string };
export function gilbertChoke(input: GilbertInput) {
  return call<GilbertResponse>('/api/v1/reservoir/choke/gilbert', { method: 'POST', body: JSON.stringify(input) });
}

export type ValveDepthInput = { pk_s: number; dp_km: number; phf: number; Gs: number };
export type ValveDepthResponse = { depth: number; method: string };
export function valveDepth(input: ValveDepthInput) {
  return call<ValveDepthResponse>('/api/v1/reservoir/gas-lift/valve-depth', { method: 'POST', body: JSON.stringify(input) });
}

export interface WellTestDrawdownRequest {
  time: number[];
  pressure: number[];
  rate: number;
  viscosity: number;
  total_compressibility: number;
  porosity: number;
  wellbore_radius: number;
  initial_pressure: number;
  net_pay: number;
  formation_volume_factor?: number;
}

export interface WellTestBuildupRequest {
  time: number[];
  pressure: number[];
  rate: number;
  viscosity: number;
  total_compressibility: number;
  porosity: number;
  wellbore_radius: number;
  producing_time: number;
  p_wf_at_shutin: number;
  net_pay: number;
  formation_volume_factor?: number;
}

export interface WellTestResult {
  permeability_md: number;
  skin: number;
  slope_psi_per_cycle: number;
  p1hr_psi: number;
  regimes: {
    radial: [number, number] | null;
    wellbore_storage: [number, number] | null;
    boundary: [number, number] | null;
    radial_slope: number | null;
    radial_std: number | null;
    notes: string[];
  };
}

export interface DrawdownResult extends WellTestResult {
  intercept_psi: number;
  radius_of_investigation_ft: number;
}

export interface BuildupResult extends WellTestResult {
  p_star_psi: number;
}

export function analyzeWellTestDrawdown(
  input: WellTestDrawdownRequest,
): Promise<DrawdownResult> {
  return call<DrawdownResult>('/api/v1/reservoir/well-test/drawdown', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export function analyzeWellTestBuildup(
  input: WellTestBuildupRequest,
): Promise<BuildupResult> {
  return call<BuildupResult>('/api/v1/reservoir/well-test/buildup', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export interface OoipUploadResult {
  session_id: string;
  well_summary: Record<string, unknown>;
  curve_list: string[];
  depth_range: number[];
}

export interface LasParseResult {
  well: Record<string, unknown>;
  curves: string[];
  row_count: number;
  depth_range: number[];
  curve_stats: Record<string, {
    min: number | null;
    max: number | null;
    mean: number | null;
    null_count: number;
  }>;
}

export function parseLasFile(file: File): Promise<LasParseResult> {
  const formData = new FormData();
  formData.append('file', file);
  return call<LasParseResult>('/api/petrophysics/las/parse', {
    method: 'POST',
    body: formData,
  });
}

export interface OoipCalculationRequest {
  session_id: string;
  area_acres: number;
  net_to_gross_cutoff: number;
  water_saturation_method: 'archie';
  archie_params: {
    a: number;
    m: number;
    n: number;
    Rw: number;
  };
}

export interface OoipCalculationResult {
  net_pay_ft: number;
  gross_pay_ft: number;
  net_to_gross: number;
  average_porosity: number;
  average_sw: number;
  ooip_bbl: number;
  ooip_stb_per_acre_ft: number;
  facies_breakdown: Record<string, Record<string, number>>;
  per_curve_summary: Record<string, Record<string, number>>;
  note: string;
}

export function uploadOoipLas(file: File): Promise<OoipUploadResult> {
  const formData = new FormData();
  formData.append('file', file);
  return call<OoipUploadResult>('/api/workflow/ooip/upload', {
    method: 'POST',
    body: formData,
  });
}

export function runOoipCalculation(
  input: OoipCalculationRequest,
): Promise<OoipCalculationResult> {
  return call<OoipCalculationResult>('/api/workflow/ooip/run', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export interface FaciesLogRecord {
  gamma: number;
  resistivity: number;
  density: number;
  porosity: number;
  depth?: number;
}

export interface FaciesClassificationResult {
  facies_predictions: Array<number | string>;
  classes: Array<number | string>;
  features_used: string[];
  training_samples_count: number;
  classification_report: Record<string, unknown> | null;
}

export function classifyFacies(
  predictData: FaciesLogRecord[],
): Promise<FaciesClassificationResult> {
  return call<FaciesClassificationResult>('/api/engine/petrophysics/facies/classify', {
    method: 'POST',
    body: JSON.stringify({ predict_data: predictData }),
  });
}