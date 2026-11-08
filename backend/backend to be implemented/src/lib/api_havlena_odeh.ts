import { call } from './api';
import type { HavlenaOdehRequest, HavlenaOdehResponse } from './types';

export async function havelnaOdeh(
  req: HavlenaOdehRequest,
): Promise<HavlenaOdehResponse> {
  return call<HavlenaOdehResponse>('/api/v1/reservoir/havlena-odeh', req);
}
