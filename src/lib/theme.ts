export function getInitialDarkMode(preference: string | null): boolean {
  return preference !== "light";
}
