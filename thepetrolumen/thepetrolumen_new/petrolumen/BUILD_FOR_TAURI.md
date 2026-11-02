BUILD FOR TAURI — PetroLúmen

What I added
- A Vite + React app scaffold at `petrolumen/tauri-web` that reuses the shared UI primitives in `petrolumen/components/ui` via an alias `@`. The Vite dev server runs on port `5173`.
- Tailwind + PostCSS config so existing Tailwind classes in the UI primitives render in the Vite preview.
- `src-tauri/tauri.conf.toml` will be updated to point at the Vite output (`../tauri-web/dist`) and to run the Vite build before packaging.
- `lib/tauri-api.ts` was updated to lazy-import the Tauri `invoke` API so it is safe in non-client builds.

How to run locally (dev)
1. From the repo root, start the Vite web preview:

```powershell
Set-Location -LiteralPath "C:\path\to\thepetrolumen\petrolumen\tauri-web"
npm install
npm run dev
```

2. In another terminal, start Tauri dev (it will connect to the Vite dev server):

```powershell
Set-Location -LiteralPath "C:\path\to\thepetrolumen\petrolumen"
npm run desktop
```

How to build the desktop artifact (packaging)

```powershell
# build the web app
Set-Location -LiteralPath "C:\path\to\thepetrolumen\petrolumen\tauri-web"
npm install
npm run build

# package backend (if needed) and build desktop
Set-Location -LiteralPath "C:\path\to\thepetrolumen\petrolumen"
npm run package:backend
npm run desktop:build
```

Notes and recommendations
- The Vite project imports shared components from `../components/ui`. Vite is configured to allow serving files outside the project root (see `vite.config.ts`).
- If you prefer keeping Next.js, we can instead run a Node server inside Tauri, but that increases bundle size and complexity. The Vite approach is simpler and yields smaller cross-platform binaries.
- After you run `npm install` for `tauri-web`, the first dev build will compile Tailwind and the shared components. If you hit path issues on Windows, use `Set-Location -LiteralPath` as shown.
