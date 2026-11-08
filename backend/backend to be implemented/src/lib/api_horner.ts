import { call } from './api';
import type { HornerRequest, HornerResponse } from './types';

export async function hornerBuildup(
  req: HornerRequest,
): Promise<HornerResponse> {
  return call<HornerResponse>('/api/v1/reservoir/horner', req);
}
