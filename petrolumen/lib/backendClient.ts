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

async function handleApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorData: ApiErrorResponse | string = `HTTP error! status: ${response.status}`;
    try {
      errorData = await response.json();
    } catch (e) {
      // If parsing JSON fails, use the status text or default message
      errorData = response.statusText || errorData;
    }
    // Construct a meaningful error message
    const errorMessage = typeof errorData === 'string'
      ? errorData
      : (typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail));

    throw new Error(errorMessage);
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

  const response = await fetch(`${API_BASE_URL}/wells/${encodeURIComponent(wellName)}/data`, {
    method: "POST",
    body: formData,
    // 'Content-Type': 'multipart/form-data' is automatically set by browser for FormData
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
  const response = await fetch(
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
  const response = await fetch(
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
  const response = await fetch(`${API_BASE_URL}/wells`);
  const data = await handleApiResponse<{ wells: string[] }>(response);
  return data.wells;
};

/**
 * (Admin) Clears all well data from the backend in-memory store.
 * @returns Promise<{ message: string }>
 */
export const adminClearAllData = async (): Promise<{ message: string }> => {
    const response = await fetch(`${API_BASE_URL}/admin/clear_all_well_data`, {
        method: "DELETE",
    });
    return handleApiResponse<{ message: string }>(response);
};
