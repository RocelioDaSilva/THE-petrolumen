# PetroLúmen Future Product & Distribution Roadmap

This roadmap captures upcoming product and distribution work. It supplements
the current platform inventory in [MODULE_STATUS.md](MODULE_STATUS.md); completed
items are marked so remaining work is clear.

## Production CSV Import

**Status: Baseline workflow implemented.** The current flow includes an
authenticated CSV import endpoint, bounded parsing/validation, duplicate
skipping, a React upload/preview/commit view, and an owner-scoped production
dashboard.

### Implemented contract

- The React sidebar has a Production Data Import view with drag-and-drop,
  file browsing, a validated preview of up to 20 rows, row-level errors, and an
  authenticated commit action.
- `POST /api/production/import/csv` accepts multipart field `file` and requires
  a bearer token. CSV headers are `well_name`, `date` (`YYYY-MM-DD`), and at
  least one of `oil_rate`, `gas_rate`, or `water_rate`. Blank rate cells are
  stored as null, but each row must contain at least one rate.
- The API enforces a 10 MB file limit and 50,000-row limit, validates the
  complete file before writing, performs parsing and database work off the
  async event loop, creates missing wells transactionally, and skips existing
  `(well_id, date)` observations.
- Imported wells are assigned to the authenticated user. The authenticated
  `GET /api/production/wells` endpoint lists only that user's wells. Existing
  wells are migrated with a nullable owner field and remain unassigned until
  explicitly claimed; they are not exposed in any user's catalog.
- The dashboard's authenticated `GET /api/production/overview` endpoint returns
  daily aggregated rates and each owned well's latest rates. Production records
  retain their import timestamp for the latest-import summary.
- The response reports received, inserted, skipped-duplicate, and created-well
  counts. Invalid files are rejected without partially importing production
  rows.

Rate units are not currently represented in `ProductionData`; the UI warns users
to confirm the project's rate convention before import. No unit conversion is
performed.

### Follow-up work

- Add explicit unit selection, conversion, and persisted unit provenance before
  using imported rates in cross-project engineering calculations.
- Add durable import-batch metadata, file digests, staged review/commit, and
  audit/rollback support.
- Add authenticated production-history query endpoints filtered by well and
  date range, then feed imported values into production trends, decline-curve
  analysis, and economics inputs. Keep sample/demo data visibly labeled.

### Verification

- Backend tests cover authorization, malformed dates/rates, upload size limits,
  duplicate skipping, and transactional persistence.
- Frontend tests cover CSV parsing, drag/drop, validation states, API upload,
  and successful import summaries.

## Near term: PyInstaller Windows executable

The current desktop launcher starts the embedded FastAPI server and serves the
React build from `dist/`. A single-file executable is a distribution target,
not yet a verified artifact.

1. **Prepare reproducible inputs**
   - Build the frontend with `npm run build` before packaging.
   - Use a supported Python version and a clean packaging virtual environment.
   - Add PyInstaller to a packaging-specific dependency set and maintain a
     project `.spec` file. Keep runtime dependencies separate from build tools.

2. **Collect the application**
   - Analyze the backend with `backend/` on PyInstaller's import path so the
     `app` package and its routes/engines are discovered.
   - Bundle the built `dist/` directory at the `_MEIPASS/dist` location
     expected by the desktop launcher.
   - Add hidden imports/data only where runtime smoke tests show a dynamically
     loaded module or package resource is missing. Pay particular attention to
     scientific Python dependencies, SQLAlchemy drivers, and WebView resources.
   - First produce and test an `onedir` build for diagnostics; switch to
     `onefile` only after the directory build is reliable.

3. **Make runtime data durable**
   - Store the SQLite database and user configuration in a writable per-user
     application-data directory, not the current working directory or the
     temporary `_MEIPASS` extraction folder.
   - Persist a protected signing secret per installation so authentication
     tokens and accounts behave predictably across app restarts.
   - Treat the Microsoft Edge WebView2 Runtime as a prerequisite or install it
     through the supported installer flow; the executable alone does not
     guarantee a compatible browser runtime on every Windows machine.

4. **Build, verify, and distribute**
   - Build the `.exe` from the maintained spec, then test on a clean Windows
     environment without the source tree or development virtual environment.
   - Verify application startup, the dynamically selected local API port,
     `/health`, React JS/CSS assets, authentication, saved-run persistence,
     upload paths, and graceful shutdown.
   - Check startup time, executable/installer size, Windows Defender behavior,
     and upgrade/uninstall behavior. Sign the release binary and installer.

Packaging is complete only after those clean-machine tests pass. PyInstaller
does not make the product's database, secret management, browser runtime, or
scientific-engine dependencies automatically portable.
