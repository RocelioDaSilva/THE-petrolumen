export async function invoke() {
  throw new Error('Tauri API is not available during server-side build')
}

export const listen = () => {
  // no-op on server
  return () => {}
}

export default { invoke, listen }

// Provide additional no-op exports commonly used from `@tauri-apps/api` so server
// bundles referencing named exports resolve at build-time without errors.
export function convertFileSrc() {
  throw new Error('Tauri convertFileSrc is not available during server-side build')
}

export function isTauri() {
  return false
}

export async function requestPermissions() {
  return []
}

export const path = {
  join: (...parts) => parts.join('/'),
}

export const dialog = {
  message: async () => null,
}

export const fs = {
  readFile: async () => '',
  writeFile: async () => ({}),
}
