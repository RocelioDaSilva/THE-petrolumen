<!-- MERGE: Combined existing `README.md` and `README.from-petrolumen.md` -->

## Existing `README.md` (thepetrolumen_new)


# PetroLúmen - Engenharia de Reservatórios

Aplicação desktop eficiente para Windows, integrando frontend moderno (React/Next.js), backend Python e empacotamento nativo com Tauri para o projeto PetroLúmen.

**Nota sobre o Backend Python:** Os exemplos de código Python neste README referem-se a módulos como `gaia_genesis.reservoir_engineering`. Esta é uma referência ao nome original do projeto Python. Se o backend Python (localizado em `../backend/` e gerenciado separadamente) também for renomeado para alinhar com "PetroLúmen", os nomes dos módulos e as importações nesses exemplos precisarão ser atualizados em conformidade pelo mantenedor do backend.

## Como rodar como aplicativo Windows

1. **Instale as dependências do frontend:**
   No diretório `petrolumen` (este diretório):
   ```bash
   # Se preferir usar npm:
   npm install
   # Ou, se preferir usar yarn:
   yarn install
   # Ou, se preferir usar pnpm:
   pnpm install
   ```
   > Certifique-se de usar apenas um gerenciador de pacotes por vez (npm, yarn ou pnpm) para evitar conflitos de dependências.

2. **Instale as dependências do backend Python:**
   O backend Python é um projeto separado e espera-se que esteja localizado em um diretório chamado `backend` ao lado deste diretório `petrolumen` (ou seja, `../backend/` a partir do diretório `petrolumen`).
   A estrutura esperada para o diretório `backend` é:
   ```
   your-main-project-folder/
   ├── petrolumen/  # Este repositório
   └── backend/     # Backend Python
       ├── main.py  # Ponto de entrada da aplicação FastAPI
       ├── requirements.txt
       └── gaia_genesis/  # Pacote principal do código Python
           └── ...
   ```
   Navegue até o diretório do backend e instale suas dependências:
   ```bash
   cd ../backend  # Ou o caminho para seu diretório de backend
   pip install -r requirements.txt
   ```

3. **Inicie o backend Python localmente:**
   A partir do diretório do backend (ex: `../backend/`), inicie seu servidor Python (FastAPI).
   ```bash
   # Estando no diretório do backend (ex: ../backend/)
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   O backend FastAPI estará disponível em `http://localhost:8000`. A aplicação frontend se comunicará com este backend para funcionalidades como upload de dados, análises, etc.

---

## `README.from-petrolumen.md` (original petrolumen)

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
