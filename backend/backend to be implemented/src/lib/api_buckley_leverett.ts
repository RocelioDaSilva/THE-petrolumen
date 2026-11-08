import { call } from './api';
import type {
  BuckLeverettRequest,
  BuckLeverettResponse,
} from './types';

export async function buckleyLeverett(
  req: BuckLeverettRequest,
): Promise<BuckLeverettResponse> {
  return call<BuckLeverettResponse>(
    '/api/v1/reservoir/buckley-leverett', req,
  );
}
