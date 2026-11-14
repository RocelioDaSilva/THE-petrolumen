import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  API_DISCONNECTED_EVENT,
  API_RECONNECTED_EVENT,
  analyzeWellTestBuildup,
  analyzeWellTestDrawdown,
  calculateEos,
  calculateFlash,
  calculateMaterialBalance,
  calculateProductionEconomics,
  calculateReservoirOperation,
  classifyFacies,
  fetchCurrentUser,
  fetchProductionOverview,
  fetchProductionWells,
  getApiAuthToken,
  importProductionCsv,
  parseLasFile,
  resolveApiBaseUrl,
  runBlackOilSimulation,
  runOoipCalculation,
  setApiAuthToken,
  uploadOoipLas,
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

  it('announces network disconnects and clears them after a successful response', async () => {
    const user = {
      id: 8,
      username: 'petro-user',
      email: 'petro@example.com',
      full_name: null,
      role: 'user',
      is_active: true,
    };
    const fetchMock = vi.fn()
      .mockRejectedValueOnce(new TypeError('fetch failed'))
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => user,
      } as Response);
    const disconnectedListener = vi.fn();
    const reconnectedListener = vi.fn();
    window.addEventListener(API_DISCONNECTED_EVENT, disconnectedListener);
    window.addEventListener(API_RECONNECTED_EVENT, reconnectedListener);
    vi.stubGlobal('fetch', fetchMock);

    try {
      await expect(fetchCurrentUser()).rejects.toMatchObject({ status: 0 });
      expect(disconnectedListener).toHaveBeenCalledOnce();
      const disconnectEvent = disconnectedListener.mock.calls[0][0] as CustomEvent<{
        detail: string;
      }>;
      expect(disconnectEvent.detail.detail).toContain('fetch failed');

      await expect(fetchCurrentUser()).resolves.toEqual(user);
      expect(reconnectedListener).toHaveBeenCalledOnce();
    } finally {
      window.removeEventListener(API_DISCONNECTED_EVENT, disconnectedListener);
      window.removeEventListener(API_RECONNECTED_EVENT, reconnectedListener);
    }
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

  it('sends well-test requests using the backend field names', async () => {
    const drawdown = {
      time: [0.1, 0.2, 0.5],
      pressure: [3400, 3320, 3250],
      rate: 500,
      viscosity: 1.2,
      total_compressibility: 0.00001,
      porosity: 0.2,
      wellbore_radius: 0.35,
      initial_pressure: 3500,
      net_pay: 30,
      formation_volume_factor: 1.2,
    };
    const buildup = {
      ...drawdown,
      producing_time: 720,
      p_wf_at_shutin: 2800,
    };
    const response = { permeability_md: 25, skin: 1.1 };
    const fetchMock = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => ({
      ok: true,
      status: 200,
      json: async () => response,
    } as Response));
    vi.stubGlobal('fetch', fetchMock);

    await expect(analyzeWellTestDrawdown(drawdown)).resolves.toEqual(response);
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/v1/reservoir/well-test/drawdown');
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual(drawdown);

    await expect(analyzeWellTestBuildup(buildup)).resolves.toEqual(response);
    expect(String(fetchMock.mock.calls[1][0])).toContain('/api/v1/reservoir/well-test/buildup');
    expect(JSON.parse(String(fetchMock.mock.calls[1][1]?.body))).toEqual(buildup);
  });

  it('sends LAS workflows as multipart and preserves Pydantic request shapes', async () => {
    const file = new File(['~Version\n~A\n1 2 3\n'], 'well.las', { type: 'text/plain' });
    const request = {
      session_id: 'session-1',
      area_acres: 100,
      net_to_gross_cutoff: 0.5,
      water_saturation_method: 'archie' as const,
      archie_params: { a: 1, m: 2, n: 2, Rw: 0.1 },
    };
    const parseResponse = {
      well: { WELL: 'Well A' },
      curves: ['PHI', 'RT'],
      row_count: 100,
      depth_range: [1000, 1100],
      curve_stats: {
        PHI: { min: 0.05, max: 0.3, mean: 0.18, null_count: 0 },
      },
    };
    const uploadResponse = {
      session_id: 'session-1',
      well_summary: {},
      curve_list: ['PHI', 'RT'],
      depth_range: [1000, 1100],
    };
    const calculationResponse = {
      net_pay_ft: 50,
      gross_pay_ft: 100,
      net_to_gross: 0.5,
      average_porosity: 0.2,
      average_sw: 0.3,
      ooip_bbl: 500000,
      ooip_stb_per_acre_ft: 100,
      facies_breakdown: {},
      per_curve_summary: {},
      note: 'OOIP estimate',
    };
    const fetchMock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => ({
      ok: true,
      status: 200,
      json: async () => {
        const url = String(input);
        if (url.includes('/petrophysics/las/parse')) return parseResponse;
        if (url.includes('/workflow/ooip/upload')) return uploadResponse;
        return calculationResponse;
      },
    } as Response));
    vi.stubGlobal('fetch', fetchMock);

    await expect(parseLasFile(file)).resolves.toEqual(parseResponse);
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/petrophysics/las/parse');
    expect(fetchMock.mock.calls[0][1]?.body).toBeInstanceOf(FormData);
    expect((fetchMock.mock.calls[0][1]?.body as FormData).get('file')).toBe(file);

    await expect(uploadOoipLas(file)).resolves.toEqual(uploadResponse);
    expect(String(fetchMock.mock.calls[1][0])).toContain('/api/workflow/ooip/upload');
    expect((fetchMock.mock.calls[1][1]?.body as FormData).get('file')).toBe(file);

    await expect(runOoipCalculation(request)).resolves.toEqual(calculationResponse);
    expect(String(fetchMock.mock.calls[2][0])).toContain('/api/workflow/ooip/run');
    expect(JSON.parse(String(fetchMock.mock.calls[2][1]?.body))).toEqual(request);
  });

  it('sends facies samples in the backend predict_data envelope', async () => {
    const samples = [{
      gamma: 35,
      resistivity: 150,
      density: 2.65,
      porosity: 0.08,
      depth: 2800,
    }];
    const response = {
      facies_predictions: [1],
      classes: [1],
      features_used: ['gamma', 'resistivity', 'density', 'porosity'],
      training_samples_count: 8,
      classification_report: null,
    };
    const fetchMock = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => ({
      ok: true,
      status: 200,
      json: async () => response,
    } as Response));
    vi.stubGlobal('fetch', fetchMock);

    await expect(classifyFacies(samples)).resolves.toEqual(response);
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/engine/petrophysics/facies/classify');
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual({ predict_data: samples });
  });

  it('routes reservoir operation calculations to the matching endpoint', async () => {
    const input = {
      q_bpd: 1000,
      glr: 600,
      choke_64: 32,
    };
    const result = { p_wh: 850, method: 'gilbert_eq_5_12' };
    const fetchMock = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => ({
      ok: true,
      status: 200,
      json: async () => result,
    } as Response));
    vi.stubGlobal('fetch', fetchMock);

    await expect(calculateReservoirOperation('choke/gilbert', input)).resolves.toEqual(result);
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/v1/reservoir/choke/gilbert');
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual(input);
  });

  it('sends the black-oil simulation using the backend payload shape', async () => {
    const input = {
      grid: { nx: 1, ny: 1, nz: 1, dx: 50, dy: 50, dz: 10 },
      porosity: [0.2],
      permeability: [100],
      rock_compressibility: 0,
      fluid_properties: {
        water_viscosity: 1,
        oil_viscosity: 2,
        gas_viscosity: 0.02,
      },
      initial_pressure: 3000,
      initial_water_saturation: [0.2],
      initial_gas_saturation: [0],
      wells: [],
      timesteps: [1],
    };
    const response = { pressure: [3000], saturations: { water: [0.2], gas: [0] }, wells: [] };
    const fetchMock = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => ({
      ok: true,
      status: 200,
      json: async () => response,
    } as Response));
    vi.stubGlobal('fetch', fetchMock);

    await expect(runBlackOilSimulation(input)).resolves.toEqual(response);
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/simulate/black-oil');
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual(input);
  });

  it('sends EOS and flash requests with component composition and EOS selection', async () => {
    const input = {
      pressure: 5_000_000,
      temperature: 250,
      eos_type: 'PR' as const,
      components: [{
        name: 'methane',
        critical_pressure: 4_599_000,
        critical_temperature: 190.56,
        acentric_factor: 0.011,
      }],
      composition: { methane: 1 },
    };
    const fetchMock = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => ({
      ok: true,
      status: 200,
      json: async () => ({ z_factor: 0.9 }),
    } as Response));
    vi.stubGlobal('fetch', fetchMock);

    await expect(calculateEos(input)).resolves.toEqual({ z_factor: 0.9 });
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/engine/pvt/eos');
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual(input);

    const flashResponse = {
      phase: 'vapor',
      vapor_fraction: 1,
      liquid_composition: null,
      vapor_composition: { methane: 1 },
      K_values: { methane: 2 },
    };
    fetchMock.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => flashResponse,
    } as Response);
    await expect(calculateFlash(input)).resolves.toEqual(flashResponse);
    expect(String(fetchMock.mock.calls[1][0])).toContain('/api/engine/pvt/flash');
    expect(JSON.parse(String(fetchMock.mock.calls[1][1]?.body))).toEqual(input);
  });

  it('sends material-balance and production-economics requests using backend schemas', async () => {
    const materialBalance = {
      reservoir_type: 'gas' as const,
      pressure_history: [4000, 3200],
      production_history: [{ gas_prod: 5_000_000, water_prod: 100 }],
    };
    const economics = {
      oil_price: 70,
      gas_price: 3,
      discount_rate: 10,
      project_life: 2,
      capex: { drilling: 1_000_000 },
      opex: { fixed_opex: 50_000 },
      tax_rate: 0.34,
      water_disposal_cost_per_bbl: 1.5,
      oil_production: [100_000, 80_000],
      gas_production: [500_000, 400_000],
      water_production: [20_000, 30_000],
    };
    const fetchMock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => ({
      ok: true,
      status: 200,
      json: async () => String(input).endsWith('/mbal')
        ? {
          reservoir_type: 'gas',
          ooip_or_ogip: 1_500_000,
          drive_indices: null,
          note: 'scalar result',
        }
        : {
          npv: 25_000,
          irr: 12,
          payout: 2,
          roi: 15,
          cashflow: [-1_000_000, 500_000, 600_000],
          cumulative_cashflow: [-1_000_000, -500_000, 100_000],
          cash_flow_details: {},
        },
    } as Response));
    vi.stubGlobal('fetch', fetchMock);

    await expect(calculateMaterialBalance(materialBalance)).resolves.toMatchObject({
      ooip_or_ogip: 1_500_000,
    });
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/engine/pvt/mbal');
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual(materialBalance);

    await expect(calculateProductionEconomics(economics)).resolves.toMatchObject({ npv: 25_000 });
    expect(String(fetchMock.mock.calls[1][0])).toContain('/api/engine/production/economics');
    expect(JSON.parse(String(fetchMock.mock.calls[1][1]?.body))).toEqual(economics);
  });
});
