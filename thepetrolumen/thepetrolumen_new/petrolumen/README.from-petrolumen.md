## Packaging the backend into the Tauri bundle (Linux/macOS)

1. Build the frontend Next app:

```bash
cd petrolumen
npm run build
```

2. Package the Python backend (creates `backend` and copies it into `src-tauri/bundle/resources`):

```bash
cd petrolumen
source .venv/bin/activate
npm run package:backend
```

3. Build the Tauri app (this will include the bundled backend):

```bash
cd petrolumen
npm run desktop:build
```

The helper script `scripts/package-backend.sh` uses PyInstaller to create a single-file executable and copies it into the Tauri resources folder so the final installer contains it.

# Gaia Genesis - Engenharia de Reservatórios

Aplicação desktop eficiente para Windows, integrando frontend moderno (React/Next.js), backend Python e empacotamento nativo com Tauri.

... (README truncated during merge)
