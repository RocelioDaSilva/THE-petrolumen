#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]
use std::process::{Child, Command};
use std::sync::{Arc, Mutex};
use tauri::{Manager, WindowEvent};

fn main() {
    let backend_process: Arc<Mutex<Option<Child>>> = Arc::new(Mutex::new(None));

    tauri::Builder::default()
        .setup({
            let backend_process = backend_process.clone();
            move |app| {
                // Cross-platform: try to spawn the bundled backend executable if present
                if let Some(resource_dir) = app.path_resolver().resource_dir() {
                    #[cfg(target_os = "windows")]
                    let exe_path = resource_dir.join("bundle").join("resources").join("backend.exe");
                    #[cfg(not(target_os = "windows"))]
                    let exe_path = resource_dir.join("bundle").join("resources").join("backend");

                    if exe_path.exists() {
                        match Command::new(&exe_path).spawn() {
                            Ok(child) => {
                                *backend_process.lock().unwrap() = Some(child);
                            }
                            Err(e) => {
                                eprintln!("Failed to spawn backend ({}): {}", exe_path.display(), e);
                            }
                        }
                    } else {
                        eprintln!("Bundled backend not found at {}", exe_path.display());
                    }
                }

                Ok(())
            }
        })
        .on_window_event({
            let backend_process = backend_process.clone();
            move |event| {
                if let WindowEvent::CloseRequested { .. } = event.event() {
                    // Try to gracefully stop the backend process if we started it
                    if let Ok(mut guard) = backend_process.lock() {
                        if let Some(mut child) = guard.take() {
                            let _ = child.kill();
                            let _ = child.wait();
                        }
                    }
                }
            }
        })
        .invoke_handler(tauri::generate_handler![])
        .run(tauri::generate_context!())
        .expect("erro ao executar aplicação");
}
