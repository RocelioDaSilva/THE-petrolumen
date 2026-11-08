import { call } from './api';
import type { GasPZRequest, GasPZResponse } from './types';

export async function gasPzAnalysis(
  req: GasPZRequest,
): Promise<GasPZResponse> {
  return call<GasPZResponse>('/api/v1/reservoir/gas-pz', req);
}
