#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use serde::Serialize;

// Define the status enum
#[derive(Serialize, Clone, Debug)]
#[serde(rename_all = "camelCase")] // Ensure it matches JS/TS casing if needed
enum ModuleStatusEnum {
    Active,
    Inactive,
    Error,
}

// Define the struct for module status
#[derive(Serialize, Clone, Debug)]
struct ModuleStatus {
    name: String,
    status: ModuleStatusEnum,
    description: String,
}

// Learn more about Tauri commands at https://tauri.app/v1/guides/features/command
#[tauri::command]
fn get_version(app: tauri::AppHandle) -> String {
    app.package_info().version.to_string()
}

#[tauri::command]
fn get_module_statuses() -> Vec<ModuleStatus> {
    // Simulate fetching data
    vec![
        ModuleStatus {
            name: "Reservoir Simulation".to_string(),
            status: ModuleStatusEnum::Active,
            description: "Eclipse, CMG, tNavigator simulators ready".to_string(),
        },
        ModuleStatus {
            name: "Production Analysis".to_string(),
            status: ModuleStatusEnum::Active,
            description: "Decline curve analysis available".to_string(),
        },
        ModuleStatus {
            name: "Optimization".to_string(),
            status: ModuleStatusEnum::Active,
            description: "History matching algorithms ready".to_string(),
        },
        ModuleStatus {
            name: "Static Modeling".to_string(),
            status: ModuleStatusEnum::Inactive, // Changed one for testing
            description: "Grid and property models loaded".to_string(),
        },
        ModuleStatus {
            name: "Uncertainty Analysis".to_string(),
            status: ModuleStatusEnum::Active,
            description: "Monte Carlo simulation ready".to_string(),
        },
        ModuleStatus {
            name: "Well Testing".to_string(),
            status: ModuleStatusEnum::Error, // Changed one for testing
            description: "Pressure analysis tools available".to_string(),
        },
        ModuleStatus {
            name: "Economic Analysis".to_string(),
            status: ModuleStatusEnum::Active,
            description: "Reserves calculation ready".to_string(),
        },
        ModuleStatus {
            name: "Visualization".to_string(),
            status: ModuleStatusEnum::Active,
            description: "3D rendering engine active".to_string(),
        },
        ModuleStatus {
            name: "AI Analytics".to_string(),
            status: ModuleStatusEnum::Active,
            description: "Machine learning models loaded".to_string(),
        },
        ModuleStatus {
            name: "Integration".to_string(),
            status: ModuleStatusEnum::Active,
            description: "Data connectors available".to_string(),
        },
    ]
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![get_version, get_module_statuses])
        .run(tauri::generate_context!())
        .expect("erro ao executar aplicação");
}
