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
  const token = typeof window !== 'undefined' ? localStorage.getItem('authToken') : null;

  const headers = new Headers(options.headers || {});
  if (token) {
    headers.append('Authorization', `Bearer ${token}`);
  }
  // Do not set Content-Type if body is FormData, browser will do it with boundary.
  // For JSON, it should be set.
  if (!(options.body instanceof FormData) && options.body) {
     if (!headers.has('Content-Type')) { // Only set if not already set
        headers.append('Content-Type', 'application/json');
     }
  }

  const response = await fetch(url, {
    ...options,
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
