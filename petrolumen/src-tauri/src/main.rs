#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

// Learn more about Tauri commands at https://tauri.app/v1/guides/features/command
#[tauri::command]
fn get_version(app: tauri::AppHandle) -> String {
    app.package_info().version.to_string()
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![get_version])
        .run(tauri::generate_context!())
        .expect("erro ao executar aplicação");
}
