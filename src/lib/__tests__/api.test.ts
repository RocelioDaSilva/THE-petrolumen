import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  fetchCurrentUser,
  fetchProductionOverview,
  fetchProductionWells,
  getApiAuthToken,
  importProductionCsv,
  resolveApiBaseUrl,
  setApiAuthToken,
} from '../api';

describe('API base URL resolution', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    setApiAuthToken(null);
  });

  it('uses the desktop launcher port from the page query', () => {
    expect(resolveApiBaseUrl('?api_port=43127')).toBe('http://127.0.0.1:43127');
  });

  it('prefers an explicitly configured API URL', () => {
    expect(resolveApiBaseUrl('?api_port=43127', 'https://api.example.test/')).toBe(
      'https://api.example.test',
    );
  });

  it('falls back to the development API URL for invalid ports', () => {
    expect(resolveApiBaseUrl('?api_port=70000')).toBe('http://localhost:8000');
    expect(resolveApiBaseUrl('')).toBe('http://localhost:8000');
  });

  it('attaches the in-memory bearer token to authenticated requests', async () => {
    const user = {
      id: 8,
      username: 'petro-user',
      email: 'petro@example.com',
      full_name: null,
      role: 'user',
      is_active: true,
    };
    const fetchMock = vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
      expect(new Headers(init?.headers).get('Authorization')).toBe('Bearer test-token');
      return {
        ok: true,
        status: 200,
        json: async () => user,
      } as Response;
    });
    vi.stubGlobal('fetch', fetchMock);
    setApiAuthToken('test-token');

    await expect(fetchCurrentUser()).resolves.toEqual(user);
    expect(getApiAuthToken()).toBe('test-token');
    expect(fetchMock).toHaveBeenCalledOnce();
  });

  it('uploads production CSV as authenticated multipart form data', async () => {
    const file = new File(['well_name,date,oil_rate\nWell A,2025-01-01,10\n'], 'production.csv', {
      type: 'text/csv',
    });
    const result = {
      rows_received: 1,
      rows_imported: 1,
      rows_skipped_duplicates: 0,
      wells_created: 1,
    };
    const fetchMock = vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
      const headers = new Headers(init?.headers);
      expect(headers.get('Authorization')).toBe('Bearer upload-token');
      expect(headers.has('Content-Type')).toBe(false);
      expect(init?.body).toBeInstanceOf(FormData);
      expect((init?.body as FormData).get('file')).toBe(file);
      return {
        ok: true,
        status: 201,
        json: async () => result,
      } as Response;
    });
    vi.stubGlobal('fetch', fetchMock);
    setApiAuthToken('upload-token');

    await expect(importProductionCsv(file)).resolves.toEqual(result);
    expect(fetchMock).toHaveBeenCalledOnce();
  });

  it('fetches owner-scoped production dashboard data with the bearer token', async () => {
    const wells = [
      { id: 1, name: 'Well A', field: null, latitude: null, longitude: null },
    ];
    const overview = {
      series: [{ date: '2025-01-01', oil_rate: 10, gas_rate: 20, water_rate: 3 }],
      latest_import_at: '2025-01-02T10:00:00+00:00',
      latest_well_rates: [
        {
          well_id: 1,
          well_name: 'Well A',
          date: '2025-01-01',
          oil_rate: 10,
          gas_rate: 20,
          water_rate: 3,
        },
      ],
    };
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      expect(new Headers(init?.headers).get('Authorization')).toBe('Bearer dashboard-token');
      return {
        ok: true,
        status: 200,
        json: async () => String(input).endsWith('/production/wells') ? wells : overview,
      } as Response;
    });
    vi.stubGlobal('fetch', fetchMock);
    setApiAuthToken('dashboard-token');

    await expect(fetchProductionWells()).resolves.toEqual(wells);
    await expect(fetchProductionOverview()).resolves.toEqual(overview);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/production/wells');
    expect(String(fetchMock.mock.calls[1][0])).toContain('/api/production/overview');
  });
});
