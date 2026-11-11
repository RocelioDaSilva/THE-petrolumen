# PetroLúmen Test & Verification Report

**Verification date:** November 11, 2026
**Environment:** Windows 10.0.19045; Node.js v24.13.1; npm 11.8.0; Python 3.14.3
**Status:** The recorded backend and frontend test suites pass, and the production bundle build succeeds when `TEMP` and `TMP` point to the project-local `.temp/` directory. Desktop GUI presentation and backend deployment remain under verification; no release-readiness or certification claim is made.

## Verified test results

| Suite | Command | Result |
|---|---|---|
| Backend | `python -m pytest backend/tests -q` | 196 passed, 8 skipped, 43 warnings |
| Engineering benchmarks | Run by `npm test` (`npx tsx src/testRunner.ts`) | 92 passed across 11 suites |
| Frontend Vitest | Run by `npm test` (`vitest run`) | 37 passed across 8 test files |

These are runner totals for the executions recorded on November 11, 2026. Passing tests do not constitute certification of every module, input range, or engineering use.

## Production build

The Windows production build was verified with the project-local temporary directory to avoid the esbuild temporary-file cleanup failure:

```powershell
New-Item -ItemType Directory -Path ".\.temp" -Force | Out-Null
$env:TEMP = (Resolve-Path ".\.temp").Path
$env:TMP = $env:TEMP
npm run build
```

- Result: **exit code 0**; TypeScript checking completed and Vite transformed 2,346 modules.
- Output: `dist/index.html` and `dist/assets/` were generated; the assets directory contained 39 files.
- The build emitted a non-fatal warning that some chunks exceed 500 kB after minification.
- `.temp/` is ignored by Git. Using it for `TEMP`/`TMP` resolved the observed Windows esbuild cleanup failure for this build; the cause of the original system-temp lock was not independently established.

## Remaining verification

- Verify the canonical installed desktop workflow, including GUI presentation and API-backed operation.
- Verify backend deployment and binding behavior for the desktop product.
