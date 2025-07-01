# PetroLúmen Windows Desktop Application Installation Guide

This guide provides step-by-step instructions to build and install the PetroLúmen desktop application on a Windows machine from the source code. This process involves setting up the frontend, the backend (which is expected to be in a separate, adjacent directory), and then building the desktop application using Tauri.

## 1. Assumed Project Structure

It's assumed your project folders are structured as follows. If your backend is located elsewhere, please adjust the paths accordingly in the commands.

```
your-main-project-folder/
├── petrolumen/  # This is the repository containing this guide
│   ├── src-tauri/
│   ├── package.json
│   └── ... (other frontend files)
└── backend/     # The Python backend code
    ├── main.py  # Or your main Python application file
    ├── requirements.txt
    └── gaia_genesis/ # Or your main Python package
        └── ...
```

## 2. Prerequisites

Before you begin, ensure you have the following software installed on your Windows machine:

*   **Node.js and npm:**
    *   Download and install from [nodejs.org](https://nodejs.org/). npm (Node Package Manager) is included with Node.js.
    *   You can verify installation by opening Command Prompt or PowerShell and typing `node -v` and `npm -v`.
*   **Python:**
    *   Download and install from [python.org](https://www.python.org/downloads/windows/).
    *   Ensure Python is added to your system's PATH during installation.
    *   You can verify installation by typing `python --version`.
*   **Rust:**
    *   Install Rust via `rustup` from [rustup.rs](https://rustup.rs). Follow the on-screen instructions.
    *   `rustup` will also install Cargo, Rust's package manager and build tool.
    *   You can verify installation by typing `rustc --version` and `cargo --version`.
*   **Tauri CLI:**
    *   Once Rust and Cargo are installed, install the Tauri Command Line Interface globally by running the following command in Command Prompt or PowerShell:
        ```bash
        cargo install tauri-cli
        ```
    *   You can verify installation by typing `cargo tauri --version`.

## 3. Backend Setup (Python)

The PetroLúmen application requires a running Python backend for its full functionality.

1.  **Navigate to your backend directory:**
    Open Command Prompt or PowerShell and change to your backend project folder.
    ```bash
    cd path\\to\\your-main-project-folder\\backend
    ```
    (Replace `path\\to\\your-main-project-folder\\backend` with the actual path to your backend directory).

2.  **Create a virtual environment (Recommended):**
    ```bash
    python -m venv venv
    venv\\Scripts\\activate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Start the backend server:**
    The command to start the server depends on how your Python backend is set up (e.g., Flask, Django, FastAPI). For a FastAPI application using Uvicorn (as referenced in the main README), the command is typically:
    ```bash
    uvicorn main:app --reload
    ```
    (Replace `main:app` if your main application instance is named differently).

    Keep this terminal window open. The backend server needs to be running for the desktop application to connect to it.

## 4. Frontend and Desktop Application Build (PetroLúmen)

1.  **Open a new terminal window** (Command Prompt or PowerShell). Do not close the terminal running your backend server.

2.  **Navigate to the `petrolumen` frontend directory:**
    ```bash
    cd path\\to\\your-main-project-folder\\petrolumen
    ```
    (Replace `path\\to\\your-main-project-folder\\petrolumen` with the actual path to the `petrolumen` directory).

3.  **Install frontend dependencies:**
    ```bash
    npm install
    ```

4.  **Build the Windows desktop application:**
    This command will first build the Next.js frontend and then use Tauri to compile the Rust application and bundle it all into a Windows installer.
    ```bash
    npm run desktop:build
    ```
    This process might take a few minutes, especially the first time, as it needs to compile Rust code and package the application.

## 5. Locate and Run the Installer

1.  **Find the installer:**
    Once the `npm run desktop:build` command completes successfully, the Windows installer (`.msi` file) will be located in:
    `petrolumen\\src-tauri\\target\\release\\bundle\\windows\\`

    The filename will typically be in the format `Petrolumen_X.Y.Z_x64_en-US.msi` (where X.Y.Z is the application version).

2.  **Install the application:**
    Double-click the `.msi` file and follow the on-screen prompts to install PetroLúmen on your system.

## 6. Running PetroLúmen

After installation, you should find PetroLúmen in your Start Menu or as a desktop shortcut (if one was created by the installer).

**Important:** Remember that the Python backend server (started in Step 3) must be running in its terminal window for the PetroLúmen desktop application to function correctly, especially for features that rely on backend data or processing.

You have now successfully built and installed the PetroLúmen Windows desktop application from the source!
