import axios from 'axios'; // Assuming axios is installed (npm install axios)
import { invoke } from '@tauri-apps/api/tauri'; // For Tauri-specific functions if needed

// --- Configuration ---
const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000/api/v1'; // Default if not in Tauri or env var

// --- Helper to get API Base URL ---
// This tries to be smart about development vs. packaged Tauri app.
// In Tauri, the backend might be a sidecar, and its port might be fixed or dynamic.
// For this setup, we assume a fixed port (8000) for the Python backend.
async function getApiBaseUrl() {
    if (window.__TAURI_IPC__) { // Check if running inside Tauri
        // If the backend port could be dynamic and passed by Tauri:
        // try {
        //   const port = await invoke('get_backend_port'); // Assuming you create such a command in Rust
        //   return `http://localhost:${port}/api/v1`;
        // } catch (error) {
        //   console.warn("Failed to invoke 'get_backend_port', falling back to default.", error);
        //   return DEFAULT_API_BASE_URL;
        // }
        // For now, assume fixed port even in Tauri:
        return DEFAULT_API_BASE_URL;
    }
    // For web development (e.g., `npm run dev` for Next.js)
    // REACT_APP_API_BASE_URL is a common convention for Create React App.
    // For Next.js, you'd use NEXT_PUBLIC_API_BASE_URL in .env.local
    return process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_API_BASE_URL;
}


// --- API Service Functions ---

/**
 * Creates a Black Oil PVT model on the backend.
 * @param {object} modelData - { name: string, pvt_data: object }
 * @returns {Promise<object>} API response
 */
export const createBlackOilModel = async (modelData) => {
    const baseUrl = await getApiBaseUrl();
    console.log(`[pvtService] Creating black oil model '${modelData.name}' at ${baseUrl}/pvt/black-oil-model`);
    const response = await axios.post(`${baseUrl}/pvt/black-oil-model`, modelData);
    return response.data;
};

/**
 * Creates a Compositional PVT model on the backend.
 * @param {object} modelData - { name: string, components: Array<object> }
 * @returns {Promise<object>} API response
 */
export const createCompositionalModel = async (modelData) => {
    const baseUrl = await getApiBaseUrl();
    console.log(`[pvtService] Creating compositional model '${modelData.name}' at ${baseUrl}/pvt/compositional-model`);
    const response = await axios.post(`${baseUrl}/pvt/compositional-model`, modelData);
    return response.data;
};

/**
 * Calculates PVT properties for a given model, pressure, and temperature.
 * @param {object} request - { model_name: string, pressure: float, temperature: float }
 * @returns {Promise<object>} PVTResult object
 */
export const fetchPVTCalculation = async (request) => {
    const baseUrl = await getApiBaseUrl();
    console.log(`[pvtService] Calculating PVT for model '${request.model_name}' at ${baseUrl}/pvt/calculate`);
    const response = await axios.post(`${baseUrl}/pvt/calculate`, request);
    return response.data;
};

/**
 * Generates a table of PVT properties over a range of pressures.
 * @param {object} request - { model_name: string, pressure_range: [start, stop, step], temperature: float }
 * @returns {Promise<Array<object>>} List of PVTResult objects
 */
export const generatePVTTable = async (request) => {
    const baseUrl = await getApiBaseUrl();
    console.log(`[pvtService] Generating PVT table for model '${request.model_name}' at ${baseUrl}/pvt/generate-table`);
    const response = await axios.post(`${baseUrl}/pvt/generate-table`, request);
    return response.data;
};

/**
 * Generates phase envelope data points for a compositional model.
 * @param {object} request - { model_name: string, temperature_range?: [start, stop, step], max_pressure?: float }
 * @returns {Promise<Array<object>>} List of phase envelope points
 */
export const fetchPhaseEnvelope = async (request) => {
    const baseUrl = await getApiBaseUrl();
    console.log(`[pvtService] Generating phase envelope for model '${request.model_name}' at ${baseUrl}/pvt/phase-envelope`);
    const response = await axios.post(`${baseUrl}/pvt/phase-envelope`, request);
    return response.data;
};

/**
 * Lists all available PVT models (currently in-memory on backend).
 * @returns {Promise<object>} { black_oil_models: [], compositional_models: [] }
 */
export const getSavedPVTModels = async () => {
    const baseUrl = await getApiBaseUrl();
    console.log(`[pvtService] Fetching saved PVT models from ${baseUrl}/pvt/models`);
    const response = await axios.get(`${baseUrl}/pvt/models`);
    return response.data;
};


// --- Mocked Model Persistence (using localStorage) ---
// This section is for UI development if backend persistence of models isn't ready.
// The backend PVTService currently stores models in-memory per instance.
// For a better UX where models persist across frontend sessions (but not backend restarts),
// localStorage can be a temporary solution.
// Ideally, the backend would save/load model definitions to its database.

const LOCAL_STORAGE_PVT_MODELS_KEY = 'petrolumen_pvtModels';

/**
 * (Mock) Gets saved PVT model definitions from localStorage.
 * This is a frontend-only mock if the backend doesn't persist models yet.
 * @returns {Promise<Array<object>>} Array of model definitions { name: string, type: string, created_at: string, ...other_params }
 */
export const getLocalMockSavedModels = async () => {
    console.log("[pvtService] Getting mock saved models from localStorage.");
    const modelsStr = localStorage.getItem(LOCAL_STORAGE_PVT_MODELS_KEY);
    return modelsStr ? JSON.parse(modelsStr) : [];
};

/**
 * (Mock) Saves a PVT model definition to localStorage.
 * @param {object} modelDetails - e.g., { name: string, type: 'black_oil' | 'compositional', pvt_data?: object, components?: Array }
 * @returns {Promise<object>} The saved model definition.
 */
export const saveLocalMockModel = async (modelDetails) => {
    console.log(`[pvtService] Saving mock model '${modelDetails.name}' to localStorage.`);
    const models = await getLocalMockSavedModels();
    const existingIndex = models.findIndex(m => m.name === modelDetails.name);

    const modelToSave = {
        ...modelDetails,
        created_at: new Date().toISOString() // Add a creation timestamp
    };

    if (existingIndex >= 0) {
        models[existingIndex] = modelToSave; // Update existing
    } else {
        models.push(modelToSave); // Add new
    }
    localStorage.setItem(LOCAL_STORAGE_PVT_MODELS_KEY, JSON.stringify(models));
    return modelToSave;
};

/**
 * (Mock) Deletes a PVT model definition from localStorage.
 * @param {string} modelName
 * @returns {Promise<boolean>} True if deleted, false otherwise.
 */
export const deleteLocalMockModel = async (modelName) => {
    console.log(`[pvtService] Deleting mock model '${modelName}' from localStorage.`);
    let models = await getLocalMockSavedModels();
    const initialLength = models.length;
    models = models.filter(m => m.name !== modelName);
    if (models.length < initialLength) {
        localStorage.setItem(LOCAL_STORAGE_PVT_MODELS_KEY, JSON.stringify(models));
        return true;
    }
    return false;
};

// Example of using invoke for a Tauri command (if you had one for backend port)
// async function getBackendPortFromTauri() {
//   if (window.__TAURI_IPC__) {
//     try {
//       return await invoke('get_backend_port_command'); // Replace with your actual command
//     } catch (e) {
//       console.error("Error invoking Tauri command for backend port:", e);
//       return null;
//     }
//   }
//   return null;
// }
