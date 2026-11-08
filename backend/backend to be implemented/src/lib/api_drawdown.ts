import { call } from './api';
import type { DrawdownRequest, DrawdownResponse } from './types';

export async function drawdownAnalysis(
  req: DrawdownRequest,
): Promise<DrawdownResponse> {
  return call<DrawdownResponse>('/api/v1/reservoir/drawdown', req);
}
