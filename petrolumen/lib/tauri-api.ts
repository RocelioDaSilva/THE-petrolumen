// import { invoke } from '@tauri-apps/api/tauri'; // Removed static import

interface FileResponse {
  success: boolean;
  message: string;
}

export const saveFile = async (path: string, contents: string): Promise<FileResponse> => {
  if (typeof window !== "undefined" && window.__TAURI_IPC__) {
    const { invoke } = await import('@tauri-apps/api/core');
    return await invoke('save_file', { path, contents });
  } else {
    console.warn("Tauri API not available. saveFile called in non-Tauri environment.");
    return { success: false, message: "Tauri API not available." };
  }
};

export const readFile = async (path: string): Promise<string> => {
  if (typeof window !== "undefined" && window.__TAURI_IPC__) {
    const { invoke } = await import('@tauri-apps/api/core');
    return await invoke('read_file', { path });
  } else {
    console.warn("Tauri API not available. readFile called in non-Tauri environment.");
    return Promise.reject("Tauri API not available.");
  }
};
