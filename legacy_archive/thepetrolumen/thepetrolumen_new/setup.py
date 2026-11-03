#!/usr/bin/env python3
"""
Cross-Platform Installer for PetroLúmen Reservoir Engineering Suite
Handles backend environment setup, database initialization, and frontend build.
"""

import os
import sys
import subprocess
import platform
import argparse
import shutil
from pathlib import Path

# --- Configuration ---
REQUIRED_PYTHON_VERSION = (3, 8) # Minimum Python 3.8
REQUIRED_NODE_VERSION = (16, 0) # Minimum Node.js 16
REQUIRED_NPM_VERSION = (7, 0)   # Minimum npm 7 (often bundled with Node 16+)

# Corrected directory names based on project structure
BACKEND_DIR_NAME = "backend"
FRONTEND_DIR_NAME = "petrolumen" # Corrected from "frontend"

# Relative paths from project root (where setup.py is)
PROJECT_ROOT_PATH = Path(__file__).resolve().parent
BACKEND_PATH = PROJECT_ROOT_PATH / BACKEND_DIR_NAME
FRONTEND_PATH = PROJECT_ROOT_PATH / FRONTEND_DIR_NAME

# Files within backend
BACKEND_ENV_FILE_NAME = ".env"
BACKEND_ENV_EXAMPLE_FILE_NAME = ".env.example"
BACKEND_REQUIREMENTS_FILE = "requirements.txt" # Relative to BACKEND_PATH
DB_DATA_SUBDIR = "db_data" # Subdirectory within BACKEND_PATH for SQLite, if used by config

# --- Color Codes for Output ---
class TermColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_c(text, color_code):
    """Prints text in a specified color."""
    # Disable colors on Windows Git Bash / MinGW as they might not render well
    if platform.system() == "Windows" and "MSYSTEM" in os.environ:
        print(text)
    else:
        print(f"{color_code}{text}{TermColors.ENDC}")

# --- Helper Functions ---
def run_command(command_list, cwd=None, check=True, shell=False, capture_output=False):
    """Executes a system command."""
    print_c(f"Executing: {' '.join(command_list) if isinstance(command_list, list) else command_list}", TermColors.OKBLUE)
    try:
        process = subprocess.run(command_list, cwd=cwd, check=check, shell=shell,
                                 text=True, capture_output=capture_output)
        if capture_output:
            return process
        return True
    except FileNotFoundError as e:
        print_c(f"Error: Command '{command_list[0]}' not found. {e}", TermColors.FAIL)
        if check: sys.exit(1)
        return False
    except subprocess.CalledProcessError as e:
        print_c(f"Error executing command: {' '.join(command_list)}. Return code: {e.returncode}", TermColors.FAIL)
        if e.stdout: print_c(f"Stdout:\n{e.stdout}", TermColors.WARNING)
        if e.stderr: print_c(f"Stderr:\n{e.stderr}", TermColors.WARNING)
        if check: sys.exit(1)
        return False
    except Exception as e:
        print_c(f"An unexpected error occurred: {e}", TermColors.FAIL)
        if check: sys.exit(1)
        return False

def check_version(tool_name, version_str, required_major, required_minor):
    """Checks if a tool's version meets requirements."""
    try:
        # Clean version string (e.g., remove 'v' prefix from Node)
        cleaned_version = version_str.lstrip('v').split('-')[0]
        major, minor = map(int, cleaned_version.split('.')[:2])
        if (major, minor) < (required_major, required_minor):
            print_c(f"{tool_name} version {required_major}.{required_minor}+ required. Found {major}.{minor}.", TermColors.WARNING)
            return False
        print_c(f"{tool_name} version {major}.{minor} found. OK.", TermColors.OKGREEN)
        return True
    except ValueError:
        print_c(f"Could not parse {tool_name} version: {version_str}", TermColors.WARNING)
        return False

# --- Environment Validation ---
def validate_environment_tools():
    """Checks for Python, Node.js, npm, and Rust."""
    print_c("\n🔍 Validating required tools...", TermColors.HEADER)
    all_ok = True

    # Python
    if sys.version_info < REQUIRED_PYTHON_VERSION:
        print_c(f"Python {REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]}+ required. Found {platform.python_version()}.", TermColors.FAIL)
        all_ok = False
    else:
        print_c(f"Python version {platform.python_version()} found. OK.", TermColors.OKGREEN)

    # Node.js
    node_proc = run_command(["node", "--version"], capture_output=True, check=False)
    if node_proc and node_proc.returncode == 0:
        if not check_version("Node.js", node_proc.stdout.strip(), REQUIRED_NODE_VERSION[0], REQUIRED_NODE_VERSION[1]):
            all_ok = False # Warning only, user might proceed
    else:
        print_c("Node.js not found. Please install from https://nodejs.org", TermColors.FAIL)
        all_ok = False

    # npm
    npm_proc = run_command(["npm", "--version"], capture_output=True, check=False)
    if npm_proc and npm_proc.returncode == 0:
        if not check_version("npm", npm_proc.stdout.strip(), REQUIRED_NPM_VERSION[0], REQUIRED_NPM_VERSION[1]):
            all_ok = False # Warning only
    else:
        print_c("npm not found. It's usually installed with Node.js.", TermColors.FAIL)
        all_ok = False

    # Rust (for Tauri)
    if not run_command(["rustc", "--version"], check=False, capture_output=True): # Just check if rustc exists
        print_c("Rust compiler (rustc) not found. Tauri requires Rust.", TermColors.WARNING)
        print_c("Please install Rust from https://rustup.rs", TermColors.WARNING)
        # Not failing hard, as user might only setup backend. Tauri build will fail later if needed.
        # Attempting auto-install of Rust is too intrusive for this script.
    else:
         print_c("Rust compiler (rustc) found. OK.", TermColors.OKGREEN)


    if not all_ok:
        print_c("Some environment checks failed or raised warnings. Please review messages above.", TermColors.FAIL)
        if not (node_proc and node_proc.returncode == 0 and npm_proc and npm_proc.returncode == 0):
             sys.exit(1) # Hard exit if Node/npm definitely missing
    else:
        print_c("✅ Tool validation passed.", TermColors.OKGREEN)

# --- Setup Functions ---
def setup_python_backend():
    """Sets up the Python backend."""
    print_c("\n🐍 Setting up Python backend...", TermColors.HEADER)

    if not BACKEND_PATH.exists() or not (BACKEND_PATH / BACKEND_REQUIREMENTS_FILE).exists():
        print_c(f"Backend directory '{BACKEND_DIR_NAME}' or '{BACKEND_REQUIREMENTS_FILE}' not found at expected location: {BACKEND_PATH}", TermColors.FAIL)
        sys.exit(1)

    # Create virtual environment
    venv_name = "venv"
    venv_path = BACKEND_PATH / venv_name

    if not venv_path.exists():
        print_c(f"Creating Python virtual environment at {venv_path}...", TermColors.OKBLUE)
        run_command([sys.executable, "-m", "venv", str(venv_path)], cwd=BACKEND_PATH) # venv path relative to BACKEND_PATH

    # Determine pip and python executables within venv
    if platform.system() == "Windows":
        pip_exe = venv_path / "Scripts" / "pip.exe"
        python_exe = venv_path / "Scripts" / "python.exe"
        alembic_exe = venv_path / "Scripts" / "alembic.exe"
    else:
        pip_exe = venv_path / "bin" / "pip"
        python_exe = venv_path / "bin" / "python"
        alembic_exe = venv_path / "bin" / "alembic"

    # Install dependencies
    print_c(f"Installing Python dependencies from {BACKEND_REQUIREMENTS_FILE}...", TermColors.OKBLUE)
    run_command([str(pip_exe), "install", "-r", BACKEND_REQUIREMENTS_FILE], cwd=BACKEND_PATH)

    # Environment file (.env)
    env_file_path = BACKEND_PATH / BACKEND_ENV_FILE_NAME
    env_example_path = BACKEND_PATH / BACKEND_ENV_EXAMPLE_FILE_NAME
    if not env_file_path.exists() and env_example_path.exists():
        print_c(f"Creating '{BACKEND_ENV_FILE_NAME}' from example...", TermColors.OKBLUE)
        shutil.copy(str(env_example_path), str(env_file_path))
        print_c(f"⚠️ Please configure database and other settings in '{env_file_path}' if needed.", TermColors.WARNING)
    elif not env_example_path.exists():
        print_c(f"Warning: '{BACKEND_ENV_EXAMPLE_FILE_NAME}' not found. Cannot create '{BACKEND_ENV_FILE_NAME}'.", TermColors.WARNING)


    # Database migrations (using Alembic executable from venv)
    print_c("Running database migrations (Alembic)...", TermColors.OKBLUE)
    # The alembic.ini and env.py should be configured to use settings.DB_PATH
    # which handles platform-specific app data directories or .env overrides.
    # The command `alembic upgrade head` should pick up `alembic.ini` in its CWD.
    run_command([str(alembic_exe), "upgrade", "head"], cwd=BACKEND_PATH)

    print_c("✅ Backend setup complete.", TermColors.OKGREEN)

def setup_tauri_frontend():
    """Sets up the Tauri frontend."""
    print_c(f"\n🖥️  Setting up {FRONTEND_DIR_NAME} frontend...", TermColors.HEADER)

    if not FRONTEND_PATH.exists() or not (FRONTEND_PATH / "package.json").exists():
        print_c(f"Frontend directory '{FRONTEND_DIR_NAME}' or 'package.json' not found at expected location: {FRONTEND_PATH}", TermColors.FAIL)
        sys.exit(1)

    # Install Node.js dependencies
    print_c("Installing Node.js dependencies (npm install)...", TermColors.OKBLUE)
    # On Windows, npm commands often need to be run with shell=True or via 'cmd /c'
    npm_shell = True if platform.system() == "Windows" else False
    run_command(["npm", "install"], cwd=FRONTEND_PATH, shell=npm_shell)

    print_c("✅ Frontend Node.js dependencies installed.", TermColors.OKGREEN)

def build_tauri_application():
    """Builds the Tauri desktop application."""
    print_c("\n🔨 Building Tauri desktop application...", TermColors.HEADER)
    if not FRONTEND_PATH.exists():
        print_c(f"Frontend directory '{FRONTEND_DIR_NAME}' not found. Cannot build.", TermColors.FAIL)
        sys.exit(1)

    # Tauri build command
    # `npm run build` (for Next.js static export) is usually part of `tauri.conf.json` beforeBuildCommand
    # So, just `npm run tauri build` should suffice.
    npm_shell = True if platform.system() == "Windows" else False
    run_command(["npm", "run", "tauri", "build"], cwd=FRONTEND_PATH, shell=npm_shell)

    print_c("✅ Tauri application build process initiated.", TermColors.OKGREEN)
    print_c(f"   Find built binaries in: {FRONTEND_PATH / 'src-tauri' / 'target' / 'release'}", TermColors.OKBLUE)


# --- Main Workflow ---
def main():
    print_c("="*60, TermColors.HEADER)
    print_c(f"{'Petrolúmen Reservoir Suite Installer':^60}", TermColors.BOLD)
    print_c("="*60, TermColors.HEADER)

    parser = argparse.ArgumentParser(description="Installer for the Petrolúmen Suite.")
    parser.add_argument('--backend-only', action='store_true', help="Only set up the Python backend.")
    parser.add_argument('--frontend-only', action='store_true', help="Only set up frontend dependencies (npm install).")
    parser.add_argument('--build-only', action='store_true', help="Only build the Tauri application (assumes frontend deps are installed).")
    parser.add_argument('--skip-validation', action='store_true', help="Skip environment tool validation (use with caution).")
    args = parser.parse_args()

    if not args.skip_validation:
        validate_environment_tools()
    else:
        print_c("Skipping environment validation as per user request.", TermColors.WARNING)

    if args.backend_only:
        setup_python_backend()
    elif args.frontend_only:
        setup_tauri_frontend()
    elif args.build_only:
        build_tauri_application()
    else: # Full setup
        setup_python_backend()
        setup_tauri_frontend() # Installs deps
        build_tauri_application() # Builds app

    print_c("\n" + "="*60, TermColors.OKGREEN)
    print_c(f"{'INSTALLATION TASKS COMPLETED':^60}", TermColors.BOLD)
    print_c("="*60, TermColors.OKGREEN)

    print_c("\nNext Steps:", TermColors.BOLD)
    print_c("1. Configure backend settings in:", TermColors.OKBLUE)
    print_c(f"   {BACKEND_PATH / BACKEND_ENV_FILE_NAME}", TermColors.UNDERLINE)
    print_c("2. To run the backend server:", TermColors.OKBLUE)
    print_c(f"   cd {BACKEND_DIR_NAME}", TermColors.OKBLUE)
    if platform.system() == "Windows":
        print_c(f"   .\\{venv_name}\\Scripts\\activate", TermColors.OKBLUE)
    else:
        print_c(f"   source {venv_name}/bin/activate", TermColors.OKBLUE)
    print_c("   uvicorn backend.gaia_genesis_new.main:app --reload  (or your configured host/port)", TermColors.OKBLUE)
    print_c("3. To run the Tauri frontend (dev mode):", TermColors.OKBLUE)
    print_c(f"   cd {FRONTEND_DIR_NAME}", TermColors.OKBLUE)
    print_c("   npm run tauri dev", TermColors.OKBLUE)
    print_c(f"4. Find production desktop app in {FRONTEND_PATH / 'src-tauri' / 'target' / 'release'}", TermColors.OKBLUE)

if __name__ == "__main__":
    main()
