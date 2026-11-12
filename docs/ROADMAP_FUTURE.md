# PetroLúmen Future Product & Distribution Roadmap

This roadmap captures product work that is not yet implemented. It supplements
the current platform inventory in [MODULE_STATUS.md](MODULE_STATUS.md) and
should be updated as features are delivered.

## Near term: Production CSV Import

### Goal

Import time-series oil, gas, and water production observations into the existing
`Well` and `ProductionData` tables, with a reviewable validation step and
traceable persistence. Do not treat production-history CSV files as LAS curves.

### End-to-end workflow

1. **React upload and preview**
   - Add a production-history import panel with drag-and-drop and file browsing.
   - Restrict input to CSV and enforce a client-side file-size limit for fast
     feedback; the API must independently enforce the authoritative limit.
   - Preview parsed headers/sample rows and let users map date, well identity,
     oil rate, gas rate, and water rate columns.
   - Require explicit rate units and date interpretation. Display validation
     errors by row and column before allowing commit.
   - Show upload/validation progress and an import summary with accepted,
     duplicate, and rejected row counts.

2. **FastAPI validation and staging**
   - Add authenticated production-import preview and commit endpoints under the
     production API.
   - Stream the uploaded file with a hard byte limit; move blocking parsing and
     validation off the async event loop.
   - Validate encoding, headers, dates, finite non-negative rates, well
     identity, declared units, and row-count/resource limits. Return bounded,
     actionable row-level errors rather than silently dropping invalid rows.
   - Stage a validated import under an import-batch identifier so the user can
     review the exact records that will be written before committing.
   - Include an idempotency key or file digest to detect accidental re-uploads.

3. **SQLAlchemy persistence**
   - Resolve the target well and commit production rows transactionally.
   - Use bulk insertion and the existing uniqueness constraint on
     `(well_id, date)` rather than querying once per row.
   - Make duplicate behavior explicit (initial default: skip existing
     observations, report their count; add update/replace only as a deliberate
     user choice).
   - Record import batch metadata: owner, original filename, digest, declared
     units, upload/commit timestamps, status, and accepted/duplicate/rejected
     counts. Retain row-level errors so an import can be audited or rolled back.
   - Decide and enforce data ownership before multi-user rollout. `Well` names
     are currently globally unique and the model has no owner relationship;
     imports must not accidentally expose one user's well data to another.

4. **Use imported history**
   - Add authenticated production-history query endpoints filtered by well and
     date range.
   - Feed real imported values into production trends, decline-curve analysis,
     and economics inputs. Keep sample/demo data visibly labeled and never
     present it as imported field data.

### Acceptance and tests

- Valid CSV imports preview and commit; malformed dates, missing columns,
  non-finite/negative rates, invalid units, oversized files, and duplicate
  dates produce explicit outcomes.
- A failed commit leaves no partial production rows. Repeating an import is
  idempotent and reports duplicates.
- Users can only preview, commit, query, and audit imports they own.
- Frontend tests cover drag/drop, mapping, preview/error states, and success
  counts; backend tests cover parsing, limits, authorization, duplicate policy,
  transaction rollback, and ownership isolation.

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
