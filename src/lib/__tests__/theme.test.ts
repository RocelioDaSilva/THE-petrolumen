import { describe, expect, it } from "vitest";
import { getInitialDarkMode } from "../theme";

describe("default theme preference", () => {
  it("uses dark mode for new users and legacy default-light values", () => {
    expect(getInitialDarkMode(null)).toBe(true);
    expect(getInitialDarkMode("0")).toBe(true);
    expect(getInitialDarkMode("dark")).toBe(true);
  });

  it("preserves an explicitly saved light theme", () => {
    expect(getInitialDarkMode("light")).toBe(false);
  });
});
