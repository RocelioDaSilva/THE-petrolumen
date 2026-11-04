/**
 * Typed HTTP client for the ppes-backed reservoir API.
 */
const BASE_URL: string =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/+$/, '') ??
  'http://localhost:8000';

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