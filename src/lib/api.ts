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

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`;
  let res: Response;
  try {
    res = await fetch(url, {
      headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
      ...init,
    });
  } catch (e) {
    throw { status: 0, detail: `Network error reaching ${url}: ${(e as Error).message}` } satisfies ApiError;
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body?.detail ?? JSON.stringify(body);
    } catch { /* keep statusText */ }
    throw { status: res.status, detail } satisfies ApiError;
  }
  return (await res.json()) as T;
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