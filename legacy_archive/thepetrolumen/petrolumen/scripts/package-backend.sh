#!/bin/bash
set -e

echo "Packaging backend with PyInstaller (Linux/macOS)..."

if [ -d ".venv" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="python3"
fi

$PYTHON -m pip install --upgrade pip
$PYTHON -m pip install pyinstaller

rm -rf dist build backend.spec || true

$PYTHON -m PyInstaller --onefile --name backend backend/main.py

DEST="src-tauri/bundle/resources"
mkdir -p "$DEST"
cp dist/backend "$DEST/backend"
echo "Backend packaged and copied to $DEST/backend"