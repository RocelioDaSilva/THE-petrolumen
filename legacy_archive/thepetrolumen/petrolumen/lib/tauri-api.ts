import { invoke } from '@tauri-apps/api/tauri';

interface FileResponse {
  success: boolean;
  message: string;
}

export const saveFile = async (path: string, contents: string): Promise<FileResponse> => {
  return await invoke('save_file', { path, contents });
};

export const readFile = async (path: string): Promise<string> => {
  return await invoke('read_file', { path });
};
