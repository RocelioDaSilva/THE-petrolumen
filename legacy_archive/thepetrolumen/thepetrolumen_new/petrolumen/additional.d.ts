// This ensures it's treated as a module, allowing augmentation of global scope.
export {};

declare global {
  interface Window {
    __TAURI_IPC__?: (message: any) => void;
    __TAURI_METADATA__?: any; // Adding this too, as it's another common Tauri global
  }
}
