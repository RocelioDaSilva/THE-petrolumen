fn main() {
  // Run tauri-build and fail early so missing resource generation errors
  // are visible during `cargo build` instead of being swallowed.
  tauri_build::build();
}
