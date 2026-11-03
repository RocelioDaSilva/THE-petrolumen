// Base URL for the backend API
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

// --- Types ---

export interface WellDataPreview {
  // Define based on expected preview structure, e.g., array of objects
  // For now, using 'any' as it depends on actual data structure
  [key: string]: any;
}

export interface WellStatistics {
  // Define based on expected statistics structure
  rows?: number;
  columns?: string[];
  description?: any; // from pandas describe()
  [key: string]: any;
}

export interface UploadResponse {
  message: string;
  well_name: string;
  files_processed: string[];
  data_preview_first_5_rows?: WellDataPreview[];
}

export interface ApiErrorResponse {
  detail: string | Array<{ loc: string[]; msg: string; type: string }>;
}

// --- Helper Functions ---

// Define a custom error class for API errors to include status
export class ApiErrorResponse extends Error {
  status: number;
  detail?: any; // Can be string or structured error from FastAPI

  constructor(message: string, status: number, detail?: any) {
    super(message);
    this.name = "ApiErrorResponse";
    this.status = status;
    this.detail = detail;
    Object.setPrototypeOf(this, ApiErrorResponse.prototype);
  }
}


async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  // Token is no longer read from localStorage. HttpOnly cookie will be sent automatically by browser.
  const headers = new Headers(options.headers || {});

  // Do not set Content-Type if body is FormData, browser will do it with boundary.
  // For JSON, it should be set.
  if (!(options.body instanceof FormData) && options.body) {
     if (!headers.has('Content-Type')) { // Only set if not already set
        headers.append('Content-Type', 'application/json');
     }
  }

  const response = await fetch(url, {
    ...options,
    credentials: 'include', // Ensure cookies are sent, 'same-origin' is often default but explicit is safer
    headers,
  });
  return response;
}


async function handleApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorDetail: any = `HTTP error! status: ${response.status}`;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorJson; // FastAPI often uses 'detail'
    } catch (e) {
      // If parsing JSON fails, use the status text or default message
      errorDetail = response.statusText || errorDetail;
    }
    // Construct a meaningful error message
    const errorMessage = typeof errorDetail === 'string'
      ? errorDetail
      : JSON.stringify(errorDetail);

    console.error("API Error:", response.status, errorMessage, errorDetail);
    throw new ApiErrorResponse(errorMessage, response.status, errorDetail);
  }
  // Handle cases where response might be empty (e.g., 204 No Content)
  if (response.status === 204) {
    return {} as T; // Or null, or handle as appropriate for your specific calls
  }
  return response.json() as Promise<T>;
}


// --- API Client Functions ---

/**
 * Uploads CSV files for a given well.
 * @param wellName The name of the well.
 * @param files The FileList object from a file input.
 * @returns Promise<UploadResponse>
 */
export const uploadWellData = async (
  wellName: string,
  files: FileList
): Promise<UploadResponse> => {
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }

  // Use fetchWithAuth
  const response = await fetchWithAuth(`${API_BASE_URL}/wells/${encodeURIComponent(wellName)}/data`, {
    method: "POST",
    body: formData,
    // Content-Type for FormData is handled by fetchWithAuth/browser
  });

  return handleApiResponse<UploadResponse>(response);
};

/**
 * Retrieves a data preview for a specific well.
 * @param wellName The name of the well.
 * @param nRows Number of rows for the preview.
 * @returns Promise<WellDataPreview[]>
 */
export const getWellDataPreview = async (
  wellName: string,
  nRows: number = 5
): Promise<WellDataPreview[]> => {
  // Use fetchWithAuth
  const response = await fetchWithAuth(
    `${API_BASE_URL}/wells/${encodeURIComponent(wellName)}/preview?n_rows=${nRows}`
  );
  const data = await handleApiResponse<{ well_name: string; preview: WellDataPreview[] }>(response);
  return data.preview;
};

/**
 * Retrieves statistics for a specific well's data.
 * @param wellName The name of the well.
 * @returns Promise<WellStatistics>
 */
export const getWellStatistics = async (wellName: string): Promise<WellStatistics> => {
  // Use fetchWithAuth
  const response = await fetchWithAuth(
    `${API_BASE_URL}/wells/${encodeURIComponent(wellName)}/statistics`
  );
  const data = await handleApiResponse<{ well_name: string; statistics: WellStatistics }>(response);
  return data.statistics;
};

/**
 * Lists all wells for which data has been loaded.
 * @returns Promise<string[]>
 */
export const listLoadedWells = async (): Promise<string[]> => {
  // Use fetchWithAuth
  const response = await fetchWithAuth(`${API_BASE_URL}/wells`);
  const data = await handleApiResponse<{ wells: string[] }>(response);
  return data.wells;
};

// --- New Auth specific client functions ---

interface TokenResponse {
  access_token: string;
  token_type: string;
}

// This is a simplified UserProfile for frontend.
// Backend's UserResponse has more fields (id, is_active, role).
// We should align these or map them appropriately.
export interface UserProfileResponse {
    username: string;
    email: string;
    full_name?: string | null;
    role: string;
    is_active: boolean;
    id: number;
}


export const loginForAccessToken = async (username: string, password: string): Promise<TokenResponse> => {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  // Auth token endpoint doesn't need Authorization header itself
  const response = await fetch(`${API_BASE_URL}/auth/token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData.toString(),
  });
  return handleApiResponse<TokenResponse>(response);
};

export const getCurrentUser = async (): Promise<UserProfileResponse> => {
  const response = await fetchWithAuth(`${API_BASE_URL}/users/me`);
  return handleApiResponse<UserProfileResponse>(response);
};

export const logoutUser = async (): Promise<void> => {
  const response = await fetchWithAuth(`${API_BASE_URL}/auth/logout`, { // Assuming this endpoint
    method: 'POST',
    // No body needed typically for logout if it's just clearing a cookie
  });
  if (!response.ok) {
    // Attempt to parse error detail if possible, otherwise use status text
    let errorDetail = `Logout failed with status: ${response.status}`;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch (e) {
      // Ignore if response is not JSON or empty
    }
    throw new ApiErrorResponse(errorDetail, response.status, errorDetail);
  }
  // No need to return data if backend just clears cookie and returns 200/204
};

// --- PVT Calculation Types ---
// Based on backend pydantic models: backend/gaia_genesis/api_v1/models/pvt_models.py

export interface ZFactorRequestData {
  pressure: number; // in psia
  temperature: number; // in Fahrenheit (°F)
  gas_specific_gravity: number;
}

export interface ZFactorResponseData {
  z_factor: number;
}

export interface FormationVolumeFactorRequestData {
  pressure: number;
  temperature: number;
  fluid_type: 'oil' | 'gas';
  api_gravity?: number | null;
  gas_specific_gravity?: number | null;
}

export interface FormationVolumeFactorResponseData {
  fvf: number; // Formation Volume Factor (Bo or Bg)
}

export interface ViscosityRequestData {
  pressure: number;
  temperature: number;
  fluid_type: 'oil' | 'gas';
  api_gravity?: number | null;
  gas_specific_gravity?: number | null;
}

export interface ViscosityResponseData {
  viscosity: number; // in cP
}

export interface SolutionGasRatioRequestData {
  pressure: number;
  temperature: number;
  api_gravity: number;
  gas_specific_gravity: number;
}

export interface SolutionGasRatioResponseData {
  rs: number; // Solution Gas-Oil Ratio (scf/stb)
}

// --- PVT Calculation API Client Functions ---

const GAIA_API_PREFIX = `${API_BASE_URL}/gaia`; // Specific prefix for these new endpoints

export const calculateZFactor = async (data: ZFactorRequestData): Promise<ZFactorResponseData> => {
  const response = await fetchWithAuth(`${GAIA_API_PREFIX}/pvt/calculate_z_factor`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return handleApiResponse<ZFactorResponseData>(response);
};

export const calculateFormationVolumeFactor = async (data: FormationVolumeFactorRequestData): Promise<FormationVolumeFactorResponseData> => {
  const response = await fetchWithAuth(`${GAIA_API_PREFIX}/pvt/calculate_formation_volume_factor`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return handleApiResponse<FormationVolumeFactorResponseData>(response);
};

export const calculateViscosity = async (data: ViscosityRequestData): Promise<ViscosityResponseData> => {
  const response = await fetchWithAuth(`${GAIA_API_PREFIX}/pvt/calculate_viscosity`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return handleApiResponse<ViscosityResponseData>(response);
};

export const calculateSolutionGasRatio = async (data: SolutionGasRatioRequestData): Promise<SolutionGasRatioResponseData> => {
  const response = await fetchWithAuth(`${GAIA_API_PREFIX}/pvt/calculate_solution_gas_ratio`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return handleApiResponse<SolutionGasRatioResponseData>(response);
};

// --- Reservoir Analysis Tools Types ---

// Material Balance
export interface OGIPRequestData {
  pressure_history: number[];
  production_history: number[];
  temperature: number;
  gas_specific_gravity: number;
}

export interface OGIPResponseData {
  ogip: number;
}

export interface STOIIPRequestData {
  pressure_history: number[];
  production_history: number[];
  temperature: number;
  api_gravity: number;
  gas_specific_gravity: number;
  bo_initial?: number | null;
  rs_initial?: number | null;
}

export interface STOIIPResponseData {
  stoiip: number;
}

// Well Testing
export interface WellTestInputBaseData {
  time_data: number[];
  pressure_data: number[];
  production_rate: number;
  fluid_viscosity: number;
  total_compressibility: number;
  formation_porosity: number;
  wellbore_radius: number;
  formation_thickness?: number | null;
}

export type BuildupTestAnalysisRequestData = WellTestInputBaseData;
export type DrawdownTestAnalysisRequestData = WellTestInputBaseData;

export interface WellTestAnalysisResponseData {
  permeability: number;
  skin_factor: number;
  slope?: number | null;
  intercept?: number | null;
}

// EUR Calculation
export interface EURCalculationRequestData {
  qi: number;
  Di: number;
  b: number;
  method_type: 'exponential' | 'harmonic' | 'hyperbolic';
}

export interface EURCalculationResponseData {
  eur: number;
}


// --- Reservoir Analysis Tools API Client Functions ---

const GAIA_RESERVOIR_TOOLS_API_PREFIX = `${GAIA_API_PREFIX}/reservoir-tools`;

export const calculateOGIP = async (data: OGIPRequestData): Promise<OGIPResponseData> => {
  const response = await fetchWithAuth(`${GAIA_RESERVOIR_TOOLS_API_PREFIX}/material-balance/ogip`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return handleApiResponse<OGIPResponseData>(response);
};

export const calculateSTOIIP = async (data: STOIIPRequestData): Promise<STOIIPResponseData> => {
  const response = await fetchWithAuth(`${GAIA_RESERVOIR_TOOLS_API_PREFIX}/material-balance/stoiip`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return handleApiResponse<STOIIPResponseData>(response);
};

export const analyzeBuildupTest = async (data: BuildupTestAnalysisRequestData): Promise<WellTestAnalysisResponseData> => {
  const response = await fetchWithAuth(`${GAIA_RESERVOIR_TOOLS_API_PREFIX}/well-testing/analyze-buildup`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return handleApiResponse<WellTestAnalysisResponseData>(response);
};

export const analyzeDrawdownTest = async (data: DrawdownTestAnalysisRequestData): Promise<WellTestAnalysisResponseData> => {
  const response = await fetchWithAuth(`${GAIA_RESERVOIR_TOOLS_API_PREFIX}/well-testing/analyze-drawdown`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return handleApiResponse<WellTestAnalysisResponseData>(response);
};

export const calculateEUR = async (data: EURCalculationRequestData): Promise<EURCalculationResponseData> => {
  const response = await fetchWithAuth(`${GAIA_RESERVOIR_TOOLS_API_PREFIX}/decline-curve/calculate-eur`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return handleApiResponse<EURCalculationResponseData>(response);
};

// --- Static Modeling Tools Types ---

export interface GridDefinitionData {
  nx: number;
  ny: number;
  nz: number;
  dx: number;
  dy: number;
  dz: number;
}

export interface WellPropertyLogData {
  md: number[];
  values: number[];
}

export interface StaticWellDataRequestData {
  well_name: string;
  x_coord: number;
  y_coord: number;
  properties: Record<string, WellPropertyLogData>; // e.g., {"Porosity": WellPropertyLogData, ...}
}

export interface VariogramCalculationRequestData {
  property_name: string;
  variogram_model_type?: 'spherical' | 'exponential' | 'gaussian';
  direction?: string; // 'omnidirectional', '0_degrees', etc.
  max_lag_distance?: number | null;
  number_of_lags?: number;
}

export interface VariogramPointData {
  lag: number;
  gamma: number;
  num_pairs: number;
}

export interface VariogramResponseData {
  property_name: string;
  experimental_variogram: VariogramPointData[];
  fitted_model_type: string;
  fitted_model_parameters: Record<string, number>; // e.g., {c0, c1, a}
  fitted_model_values?: number[] | null;
}

export interface KrigingRequestData {
  property_name: string;
}

export interface KrigingResponseData {
  property_name: string;
  interpolated_grid_values: number[][]; // Assuming 2D grid for now
  kriging_std_dev_grid_values?: number[][] | null;
  grid_dimensions?: [number, number] | null; // [nx, ny]
}

// Rock Physics
export interface RockPhysicsRequestBaseData {
  model_type: 'gassmann' | 'hertz_mindlin';
  porosity: number;
}

export interface GassmannRequestData extends RockPhysicsRequestBaseData {
  model_type: 'gassmann';
  k_dry: number;
  k_matrix: number;
  k_fluid: number;
  g_matrix: number;
}

export interface HertzMindlinRequestData extends RockPhysicsRequestBaseData {
  model_type: 'hertz_mindlin';
  g_matrix: number;
  k_matrix: number;
  critical_porosity?: number;
  effective_pressure?: number;
  poisson_ratio_matrix?: number;
}

export type RockPhysicsModelsUnion = GassmannRequestData | HertzMindlinRequestData;

export interface RockPhysicsResponseData {
  model_type: string;
  k_saturated: number;
  g_saturated: number;
  vp: number;
  vs: number;
  rho_bulk: number;
}

// NMR Analysis
export interface NMRAnalysisRequestData {
  well_name: string;
  t2_distribution: number[];
  t2_times: number[];
}

export interface NMRAnalysisResponseData {
  well_name: string;
  t2_log_mean: number;
  bulk_volume_irreducible: number;
  free_fluid_volume: number;
  pore_sizes_microns?: number[] | null;
  permeability_coates_md?: number | null;
  permeability_sdr_md?: number | null;
  capillary_pressure_psi_proxy?: number[] | null;
  t2_distribution_echo: number[];
  t2_times_echo: number[];
}


// --- Static Modeling Tools API Client Functions ---

const GAIA_STATIC_MODELING_API_PREFIX = `${GAIA_API_PREFIX}/static-modeling`;

export const defineStaticGrid = async (data: GridDefinitionData): Promise<{ message: string; grid_definition: GridDefinitionData }> => {
  const response = await fetchWithAuth(`${GAIA_STATIC_MODELING_API_PREFIX}/grid`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return handleApiResponse<{ message: string; grid_definition: GridDefinitionData }>(response);
};

export const addStaticWellData = async (data: StaticWellDataRequestData): Promise<{ message: string }> => {
  const response = await fetchWithAuth(`${GAIA_STATIC_MODELING_API_PREFIX}/well-data`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return handleApiResponse<{ message: string }>(response);
};

export const calculatePropertyVariogram = async (data: VariogramCalculationRequestData): Promise<VariogramResponseData> => {
  const response = await fetchWithAuth(`${GAIA_STATIC_MODELING_API_PREFIX}/variogram`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return handleApiResponse<VariogramResponseData>(response);
};

export const performKrigingInterpolation = async (data: KrigingRequestData): Promise<KrigingResponseData> => {
  const response = await fetchWithAuth(`${GAIA_STATIC_MODELING_API_PREFIX}/kriging`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return handleApiResponse<KrigingResponseData>(response);
};

export const calculateRockPhysicsProperties = async (data: RockPhysicsModelsUnion): Promise<RockPhysicsResponseData> => {
  const response = await fetchWithAuth(`${GAIA_STATIC_MODELING_API_PREFIX}/rock-physics`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return handleApiResponse<RockPhysicsResponseData>(response);
};

export const performNMRAnalysis = async (data: NMRAnalysisRequestData): Promise<NMRAnalysisResponseData> => {
  const response = await fetchWithAuth(`${GAIA_STATIC_MODELING_API_PREFIX}/nmr-analysis`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return handleApiResponse<NMRAnalysisResponseData>(response);
};
