// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{Manager, api::path::{app_data_dir, resolve_resource, BaseDirectory}, command, AppHandle, Wry};
use std::{
    path::{Path, PathBuf},
    process::{Command as StdCommand, Stdio, Child}, // Renamed to avoid conflict with tauri::Command
    sync::Mutex, // For managing the backend process handle
    io::{BufReader, BufRead, Write}, // For reading backend stdout/stderr
    thread, // For running backend process management in a separate thread
};

// --- Global State for Backend Process ---
// This will hold the handle to the Python backend process so we can manage it.
struct BackendProcess(Mutex<Option<Child>>);

impl BackendProcess {
    fn set(&self, child: Child) {
        let mut process_guard = self.0.lock().unwrap();
        *process_guard = Some(child);
    }

    fn clear(&self) {
        let mut process_guard = self.0.lock().unwrap();
        *process_guard = None;
    }

    fn kill_if_running(&self) {
        let mut process_guard = self.0.lock().unwrap();
        if let Some(mut child) = process_guard.take() {
            println!("Attempting to kill existing backend process: {}", child.id());
            match child.kill() {
                Ok(_) => {
                    println!("Backend process {} killed successfully.", child.id());
                    match child.wait() { // Wait for the process to exit
                        Ok(status) => println!("Backend process {} exited with status: {}", child.id(), status),
                        Err(e) => println!("Failed to wait for backend process {}: {}", child.id(), e),
                    }
                }
                Err(e) => {
                    println!("Failed to kill backend process {}: {}. It might have already exited.", child.id(), e);
                    // If killing fails, it might still be running or already gone.
                    // Put it back if we couldn't confirm it's dead, so subsequent calls might try again.
                    // Or, assume it's gone if kill fails. For now, let's assume it's gone.
                }
            }
        } else {
            println!("No backend process was running to kill.");
        }
    }
}


// --- Tauri Commands ---
#[command]
fn get_platform_specific_db_path(app_handle: AppHandle) -> Result<String, String> {
    // This command provides the path where the app *should* store its data.
    // The actual database might be copied here from resources on first run.
    let path = app_data_dir(&app_handle.config())
        .ok_or_else(|| "Failed to get app data directory".to_string())?
        .join("Petrolumen") // App-specific subdirectory
        .join("database.db"); // The database file name

    // Ensure the directory exists
    if let Some(parent_dir) = path.parent() {
        if !parent_dir.exists() {
            std::fs::create_dir_all(parent_dir)
                .map_err(|e| format!("Failed to create app data parent directory: {}", e))?;
        }
    }
    Ok(path.to_string_lossy().into_owned())
}

#[command]
fn get_resource_path(app_handle: AppHandle, resource_name: String) -> Result<String, String> {
    resolve_resource(&app_handle.config(), app_handle.package_info(), &resource_name, None)
        .ok_or_else(|| format!("Failed to resolve resource: {}", resource_name))
        .map(|path| path.to_string_lossy().into_owned())
}


// --- Main Application Setup ---
fn main() {
    let context = tauri::generate_context!(); // Generates context from tauri.conf.json

    tauri::Builder::default()
        .manage(BackendProcess(Mutex::new(None))) // Add backend process handle to Tauri's state
        .setup(|app| {
            let app_handle = app.handle();
            let backend_proc_state = app_handle.state::<BackendProcess>();

            // --- Determine Paths ---
            let app_data_root = app_data_dir(&app.config())
                .expect("Failed to get app data directory for Petrolumen.");

            let petrolumen_app_data_dir = app_data_root.join("Petrolumen");
            std::fs::create_dir_all(&petrolumen_app_data_dir)
                .expect("Failed to create Petrolumen app data directory.");

            let db_path_in_app_data = petrolumen_app_data_dir.join("database.db");

            // Copy bundled template database if it exists and target DB doesn't
            // The resource path is relative to src-tauri/ or what's defined in tauri.conf.json resources
            // Based on `tauri.conf.json` `resources: ["../../backend/database.db"]`
            // This path means the template DB is expected at `project_root/backend/database.db`
            // when `tauri build` is run from `project_root/petrolumen/`.
            match app.path_resolver().resolve_resource("../../backend/database.db") {
                Some(resource_path) if resource_path.exists() => {
                    if !db_path_in_app_data.exists() {
                        println!("Template database found at {:?}, copying to {:?}", resource_path, db_path_in_app_data);
                        match std::fs::copy(&resource_path, &db_path_in_app_data) {
                            Ok(_) => println!("Template database copied successfully."),
                            Err(e) =>eprintln!("ERROR: Failed to copy template database: {}",e),
                        }
                    } else {
                        println!("Database already exists at {:?}, not copying template.", db_path_in_app_data);
                    }
                }
                _ => {
                    println!("WARNING: Template database resource '../../backend/database.db' not found or path is incorrect. A new DB will be created by Alembic if it doesn't exist at the app_data path.");
                }
            }

            // --- Backend Executable Path ---
            // This path needs to point to your Python backend executable or entry script.
            // If Python is bundled (e.g. with PyInstaller/Nuitka), this points to that binary.
            // If running a .py script, it's `python` and the script path.
            // For development, you might run the .py script directly.
            // For production, this would be a bundled executable.

            // Option 1: Bundled Python executable (adjust name and location)
            // This assumes `backend_main_executable` is placed in resources by your build process.
            // let backend_exe_name = if cfg!(windows) { "petrolumen_backend.exe" } else { "petrolumen_backend" };
            // let backend_path = app.path_resolver()
            //     .resolve_resource(format!("bin/{}", backend_exe_name)) // Example path in resources
            //     .expect("Failed to resolve backend executable resource");

            // Option 2: Running a Python script (more for dev or if Python is a prerequisite)
            // This assumes `python` or `python3` is in PATH, and the script is a resource.
            let python_executable = if cfg!(windows) { "python.exe" } else { "python3" }; // Or just "python"

            // The main.py for FastAPI is now at `backend/gaia_genesis_new/main.py`
            // If this `main.py` is a resource, its path needs to be resolved.
            // Let's assume it's bundled as `backend_script.py` in resources for simplicity,
            // or we use a relative path if the backend source is copied into the app bundle.
            // The `setup.py` `entry_points` creates `petrolumen-backend` script in venv/bin.
            // If we ship the venv or a Python distribution, we could call that.
            // This is the trickiest part of sidecar setup.

            // For now, let's assume a simple case:
            // The backend is started by running the `main.py` script using a Python interpreter
            // that is expected to be on the system PATH.
            // The script itself is copied as a resource.
            // Resource path in tauri.conf.json should be like: `../../backend/gaia_genesis_new/main.py`
            // and perhaps `../../backend/database.py`, etc. or the whole `backend` dir.

            let backend_script_resource_path = "../../backend/gaia_genesis_new/main.py";
            let backend_main_script_path = app.path_resolver()
                .resolve_resource(backend_script_resource_path)
                .ok_or_else(|| format!("Backend script resource '{}' not found. Check tauri.conf.json resources.", backend_script_resource_path))
                .unwrap(); // Expect for now

            println!("Attempting to start backend script: {:?}", backend_main_script_path);
            println!("Using Python interpreter: {}", python_executable);
            println!("Effective DATABASE_URL for backend: {}", db_path_in_app_data.to_string_lossy());


            // --- Start Backend Process ---
            let mut cmd = StdCommand::new(python_executable);
            cmd.arg(backend_main_script_path); // Pass the script path to python interpreter

            // Set environment variables for the backend process
            cmd.env("TAURI_ENV", "production"); // Signal to Python it's running in production mode
            cmd.env("DATABASE_URL", db_path_in_app_data.to_string_lossy().to_string());
            // If backend needs to find other files relative to itself, set PYTHONPATH or CWD.
            // Setting CWD to where the script is, if it uses relative paths for other files:
            if let Some(script_dir) = backend_main_script_path.parent() {
                 cmd.current_dir(script_dir);
                 println!("Set backend CWD to: {:?}", script_dir);
            }


            cmd.stdout(Stdio::piped()); // Capture stdout
            cmd.stderr(Stdio::piped()); // Capture stderr

            match cmd.spawn() {
                Ok(child) => {
                    println!("Backend process started successfully. PID: {}", child.id());
                    let child_stdout = child.stdout.expect("Failed to get backend stdout");
                    let child_stderr = child.stderr.expect("Failed to get backend stderr");
                    let app_handle_clone_stdout = app_handle.clone();
                    let app_handle_clone_stderr = app_handle.clone();

                    // Thread to read and emit stdout
                    thread::spawn(move || {
                        let reader = BufReader::new(child_stdout);
                        for line in reader.lines() {
                            if let Ok(l) = line {
                                println!("[Backend STDOUT]: {}", l);
                                app_handle_clone_stdout.emit_all("backend-stdout", l.clone()).unwrap();
                            }
                        }
                    });
                    // Thread to read and emit stderr
                    thread::spawn(move || {
                        let reader = BufReader::new(child_stderr);
                        for line in reader.lines() {
                            if let Ok(l) = line {
                                eprintln!("[Backend STDERR]: {}", l); // Use eprintln for stderr
                                app_handle_clone_stderr.emit_all("backend-stderr", l.clone()).unwrap();
                            }
                        }
                    });
                    backend_proc_state.set(child); // Store the child process handle
                }
                Err(e) => {
                    eprintln!("ERROR: Failed to start backend process: {}", e);
                    // Emit an event to frontend about failure?
                    app_handle.emit_all("backend-status", format!("failed: {}", e)).unwrap();
                }
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_platform_specific_db_path,
            get_resource_path
        ])
        .build(context)
        .expect("Error while building Tauri application")
        .run(|app_handle, event| match event {
            tauri::RunEvent::ExitRequested { api, .. } => {
                // App is about to exit, kill the backend process
                println!("Tauri RunEvent::ExitRequested detected. Killing backend process.");
                let backend_proc_state = app_handle.state::<BackendProcess>();
                backend_proc_state.kill_if_running();
                api.prevent_exit(); // Optional: if you need to do more async cleanup
                                   // If not preventing, Tauri will exit after this handler.
            }
            tauri::RunEvent::Exit => {
                 println!("Tauri RunEvent::Exit. Ensuring backend is stopped.");
                 let backend_proc_state = app_handle.state::<BackendProcess>();
                 backend_proc_state.kill_if_running(); // Ensure it's killed on final exit too
            }
            _ => {}
        });
}
