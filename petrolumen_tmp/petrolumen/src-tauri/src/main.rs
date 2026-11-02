#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use std::collections::HashSet;
use std::io::{BufRead, BufReader, Write};
use std::net::{TcpListener, TcpStream};
use std::fs::OpenOptions;
use std::time::Duration;
use std::thread;
use std::path::PathBuf;
use tauri::Manager;
use tauri::Emitter;

#[tauri::command]
fn get_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

#[tauri::command]
fn get_server_port(state: tauri::State<'_, Arc<Mutex<Option<u16>>>>) -> Option<u16> {
    let port = *state.lock().unwrap();
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(exe_dir.join("next_start.log")) {
                let _ = writeln!(f, "get_server_port invoked -> {:?}", port);
            }
        }
    }
    port
}

#[tauri::command]
fn frontend_alive() -> bool {
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(exe_dir.join("next_start.log")) {
                let _ = writeln!(f, "frontend_alive invoked");
            }
        }
    }
    true
}

fn main() {
    let server_process: Arc<Mutex<Option<Child>>> = Arc::new(Mutex::new(None));
    let server_port: Arc<Mutex<Option<u16>>> = Arc::new(Mutex::new(None));
    // Track which windows we've already emitted `next-ready` to so we
    // don't repeatedly cause client-side redirects when pages reload.
    let emitted_next_ready: Arc<Mutex<HashSet<String>>> = Arc::new(Mutex::new(HashSet::new()));
    // create per-closure clones so each closure/thread can own a clone
    let emitted_next_ready_for_setup = emitted_next_ready.clone();
    let emitted_next_ready_for_on_page_load = emitted_next_ready.clone();

    // Early startup diagnostic
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(exe_dir.join("next_start.log")) {
                let _ = writeln!(f, "petrolumen-desktop starting");
            }
        }
    }

    tauri::Builder::default()
        .manage(server_port.clone())
        .setup({
            let server_process = server_process.clone();
            let server_port = server_port.clone();
            move |app| {
                let app_handle = app.handle();
                // Log how many windows are configured in the generated context
                if let Some(p) = std::env::current_exe().ok().and_then(|p| p.parent().map(|d| d.join("next_start.log"))) {
                    if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                        let _ = writeln!(f, "Config windows count: {}", app_handle.config().app.windows.len());
                    }
                }

                // Spawn the bundled Next standalone server in a background thread at startup.
                if let Some(p) = std::env::current_exe().ok().and_then(|p| p.parent().map(|d| d.join("next_start.log"))) {
                    if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                        let _ = writeln!(f, "setup: spawning background thread");
                    }
                }

                // If the generated context has no configured windows (common when
                // bundling assets separately), create a `main` window programmatically
                // and attach an `index.html` webview so the loader runs and can
                // receive `next-ready` events.
                // Log whether a `main` webview is already present.
                if let Some(p) = std::env::current_exe().ok().and_then(|p| p.parent().map(|d| d.join("next_start.log"))) {
                    if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                        let _ = writeln!(f, "get_webview_window('main') at setup -> {}", app_handle.get_webview_window("main").is_some());
                    }
                }

                if app_handle.config().app.windows.is_empty() && app_handle.get_webview_window("main").is_none() {
                    if let Some(p) = std::env::current_exe().ok().and_then(|p| p.parent().map(|d| d.join("next_start.log"))) {
                        if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                            let _ = writeln!(f, "No configured windows; creating programmatic main window");
                        }
                    }

                    // Build a WebviewBuilder to load the embedded `index.html` and
                    // create the window with that webview so the Tauri JS bridge
                    // is injected correctly.
                    match tauri::window::WindowBuilder::new(app, "main")
                        .title("PetroLúmen")
                        .inner_size(1024.0, 768.0)
                        .resizable(true)
                        .build()
                    {
                        Ok(window) => {
                            // create a webview that loads the embedded `index.html`
                            let size = window.inner_size()
                                .map(|s| tauri::LogicalSize::new(s.width as f64, s.height as f64))
                                .unwrap_or(tauri::LogicalSize::new(1024.0, 768.0));
                            let webview_builder = tauri::webview::WebviewBuilder::new("main", tauri::WebviewUrl::App("index.html".into()));
                            match window.add_child(webview_builder, tauri::LogicalPosition::new(0.0, 0.0), size) {
                                Ok(_) => {
                                    if let Some(p) = std::env::current_exe().ok().and_then(|p| p.parent().map(|d| d.join("next_start.log"))) {
                                        if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                                            let _ = writeln!(f, "Created programmatic loader window: main");
                                        }
                                    }
                                }
                                Err(e) => {
                                    if let Some(p) = std::env::current_exe().ok().and_then(|p| p.parent().map(|d| d.join("next_start.log"))) {
                                        if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                                            let _ = writeln!(f, "failed to add webview to programmatic window: {}", e);
                                        }
                                    }
                                }
                            }
                        }
                        Err(e) => {
                            if let Some(p) = std::env::current_exe().ok().and_then(|p| p.parent().map(|d| d.join("next_start.log"))) {
                                if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                                    let _ = writeln!(f, "failed to create programmatic window: {}", e);
                                }
                            }
                        }
                    }
                }

                // (window-created listener removed; relying on on_page_load + loader diagnostics)
                let server_process = server_process.clone();
                let server_port = server_port.clone();
                let emitted_next_ready = emitted_next_ready_for_setup.clone();
                let app_handle = app_handle.clone();
                let app_handle_for_spawn = app_handle.clone();
                std::thread::spawn(move || {
                    // Look for server.js in several likely locations relative to the executable
                    let mut found: Option<PathBuf> = None;
                    if let Ok(exe_path) = std::env::current_exe() {
                        if let Some(exe_dir) = exe_path.parent() {
                            let candidates = [
                                exe_dir.join("bundle").join("resources").join("next").join("server.js"),
                                exe_dir.join("bundle").join("resources").join("next").join("standalone").join("server.js"),
                                exe_dir.join("resources").join("next").join("server.js"),
                                exe_dir.join("next").join("server.js"),
                                exe_dir.join("..").join("bundle").join("resources").join("next").join("server.js"),
                                exe_dir.join("..").join("..").join("src-tauri").join("bundle").join("resources").join("next").join("server.js"),
                                exe_dir.join("..").join("..").join("bundle").join("resources").join("next").join("server.js"),
                            ];
                            for c in candidates.iter() {
                                if c.exists() {
                                    found = Some(c.to_path_buf());
                                    break;
                                }
                            }
                        }
                    }

                    if let Some(server_js) = found {
                        // Prepare a log file next to the executable for diagnostics
                        let log_path: Option<PathBuf> = std::env::current_exe().ok().and_then(|p| p.parent().map(|d| d.join("next_start.log")));

                        // Pick a free ephemeral port (or fallback to 3000)
                        let port = match TcpListener::bind(("127.0.0.1", 0)) {
                            Ok(l) => l.local_addr().map(|a| a.port()).unwrap_or(3000),
                            Err(_) => 3000,
                        };

                        let start_msg = format!("Starting Next standalone server on port {}", port);
                        eprintln!("{}", start_msg);
                        if let Some(p) = &log_path {
                            if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                                let _ = writeln!(f, "{}", start_msg);
                            }
                        }

                        // spawn node server
                        let mut cmd = Command::new("node");
                        // ensure the child runs with its working dir set to the server.js folder
                        if let Some(server_dir) = server_js.parent() {
                            cmd.current_dir(server_dir);
                            // also set NODE_PATH to server_dir/node_modules to help module resolution
                            let node_modules = server_dir.join("node_modules");
                            cmd.env("NODE_PATH", node_modules);
                        }
                        cmd.arg(&server_js)
                            .env("PORT", port.to_string())
                            .stdout(Stdio::piped())
                            .stderr(Stdio::piped());

                        match cmd.spawn() {
                            Ok(mut child) => {
                                // forward child stdout
                                if let Some(stdout) = child.stdout.take() {
                                    let path_for_stdout = log_path.clone();
                                    let _ = thread::spawn(move || {
                                        let mut r = BufReader::new(stdout);
                                        let mut line = String::new();
                                        while let Ok(bytes) = r.read_line(&mut line) {
                                            if bytes == 0 { break }
                                            let l = format!("[next stdout] {}", line.trim_end());
                                            eprintln!("{}", l);
                                            if let Some(p) = &path_for_stdout {
                                                if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                                                    let _ = writeln!(f, "{}", l);
                                                }
                                            }
                                            line.clear();
                                        }
                                    });
                                }

                                // forward child stderr
                                if let Some(stderr) = child.stderr.take() {
                                    let path_for_stderr = log_path.clone();
                                    let _ = thread::spawn(move || {
                                        let mut r = BufReader::new(stderr);
                                        let mut line = String::new();
                                        while let Ok(bytes) = r.read_line(&mut line) {
                                            if bytes == 0 { break }
                                            let l = format!("[next stderr] {}", line.trim_end());
                                            eprintln!("{}", l);
                                            if let Some(p) = &path_for_stderr {
                                                if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                                                    let _ = writeln!(f, "{}", l);
                                                }
                                            }
                                            line.clear();
                                        }
                                    });
                                }

                                *server_process.lock().unwrap() = Some(child);

                                // Wait for the server to accept connections (timeout ~15s)
                                let start = std::time::Instant::now();
                                let mut started = false;
                                while start.elapsed() < Duration::from_secs(15) {
                                    if TcpStream::connect(("127.0.0.1", port)).is_ok() {
                                        started = true;
                                        break;
                                    }
                                    thread::sleep(Duration::from_millis(100));
                                }

                                if started {
                                    // store the port in shared state for use by the loader poller
                                    *server_port.lock().unwrap() = Some(port);
                                        // Log server readiness
                                        eprintln!("Server ready on port {}", port);
                                        if let Some(p) = &log_path {
                                            if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                                                let _ = writeln!(f, "Server ready on port {}", port);
                                            }
                                        }

                                        // Emit the readiness only to the programmatic loader window
                                        // (if present) and only once per-window to avoid redirect loops.
                                        if let Some(window) = app_handle_for_spawn.get_webview_window("main") {
                                            let label = window.label().to_string();
                                            let mut emitted = emitted_next_ready.lock().unwrap();
                                            if emitted.insert(label.clone()) {
                                                if let Some(p) = &log_path {
                                                    if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                                                        let _ = writeln!(f, "Emitting next-ready to window {}", label);
                                                    }
                                                }
                                                let _ = window.emit("next-ready", port);
                                            } else if let Some(p) = &log_path {
                                                if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                                                    let _ = writeln!(f, "Skipping emit to window {} — already emitted", label);
                                                }
                                            }
                                        }

                                    // Small retry emits to help late-registered listeners pick up the event.
                                    let app_handle_retry = app_handle_for_spawn.clone();
                                    let log_path_retry = log_path.clone();
                                    let port_retry = port;
                                    let emitted_retry = emitted_next_ready.clone();
                                    let _ = thread::spawn(move || {
                                        thread::sleep(Duration::from_millis(300));
                                        if let Some(window) = app_handle_retry.get_webview_window("main") {
                                            let label = window.label().to_string();
                                            let mut emitted = emitted_retry.lock().unwrap();
                                            if emitted.insert(label.clone()) {
                                                let _ = window.emit("next-ready", port_retry);
                                                if let Some(p) = &log_path_retry {
                                                    if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                                                        let _ = writeln!(f, "Retry emit next-ready attempt 1 for {} to window {}", port_retry, label);
                                                    }
                                                }
                                            }
                                        }
                                        thread::sleep(Duration::from_millis(700));
                                        if let Some(window) = app_handle_retry.get_webview_window("main") {
                                            let label = window.label().to_string();
                                            let mut emitted = emitted_retry.lock().unwrap();
                                            if emitted.insert(label.clone()) {
                                                let _ = window.emit("next-ready", port_retry);
                                                if let Some(p) = &log_path_retry {
                                                    if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                                                        let _ = writeln!(f, "Retry emit next-ready attempt 2 for {} to window {}", port_retry, label);
                                                    }
                                                }
                                            }
                                        }
                                    });
                                } else {
                                    if let Some(p) = &log_path {
                                        if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                                            let _ = writeln!(f, "Next server did not start within timeout on port {}", port);
                                        }
                                    }
                                }
                            }
                            Err(e) => {
                                if let Some(p) = &log_path {
                                    if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                                        let _ = writeln!(f, "Failed to spawn Next standalone server: {}", e);
                                    }
                                }
                            }
                        }
                    } else {
                        if let Some(p) = std::env::current_exe().ok().and_then(|p| p.parent().map(|d| d.join("next_start.log"))) {
                            if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                                let _ = writeln!(f, "Standalone Next server not found in expected locations");
                            }
                        }
                    }
                });

                // Let Tauri create the configured windows (including `main`) so
                // the normal startup lifecycle and `on_page_load` handlers run.

                // Small delayed probe to log whether the `main` window exists
                // after startup. This helps diagnose races between window
                // creation and event listener registration in the loader.
                {
                    let app_handle_inspect = app_handle.clone();
                    let log_path_inspect = std::env::current_exe().ok().and_then(|p| p.parent().map(|d| d.join("next_start.log")));
                    std::thread::spawn(move || {
                        thread::sleep(Duration::from_millis(1200));
                        let has_main = app_handle_inspect.get_webview_window("main").is_some();
                        if let Some(p) = &log_path_inspect {
                            if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                                let _ = writeln!(f, "Delayed probe: App has main window: {}", has_main);
                            }
                        }
                    });
                }

                Ok(())
            }
        })
        .on_page_load(move |window, _payload| {

            // Diagnostic entry when the webview loads
            let log_path = std::env::current_exe().ok().and_then(|p| p.parent().map(|d| d.join("next_start.log")));
            if let Some(p) = &log_path {
                if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                    let _ = writeln!(f, "on_page_load fired");
                }
            }
                if let Some(port) = *server_port.lock().unwrap() {
                if let Some(p) = &log_path {
                    if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                        let _ = writeln!(f, "on_page_load sees port {}", port);
                    }
                }
                // If the backend already has a port, notify the window so the
                // loader's event listener or poller can navigate to the server.
                // Only emit once per-window to avoid redirect loops when pages
                // reload and `on_page_load` fires repeatedly.
                let label = window.label().to_string();
                let mut emitted = emitted_next_ready_for_on_page_load.lock().unwrap();
                if emitted.insert(label.clone()) {
                    let _ = window.emit("next-ready", port);
                    if let Some(p) = &log_path {
                        if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                            let _ = writeln!(f, "on_page_load emitted next-ready for window {}", label);
                        }
                    }
                } else if let Some(p) = &log_path {
                    if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                        let _ = writeln!(f, "on_page_load skipping next-ready for window {} (already emitted)", label);
                    }
                }
            } else if let Some(p) = &log_path {
                if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(p) {
                    let _ = writeln!(f, "on_page_load: server_port not set");
                }
            }

            // The loader HTML already implements a poller and listens for
            // the `next-ready` event; no JS injection is required here.
        })
        .invoke_handler(tauri::generate_handler![get_version, get_server_port, frontend_alive])
        .run(tauri::generate_context!())
        .expect("failed to run tauri application");
}
