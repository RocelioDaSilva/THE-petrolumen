# PetroLúmen Test & Verification Report

**Verification date:** November 11, 2026
**Environment:** Windows 10.0.19045; Node.js v24.13.1; npm 11.8.0; Python 3.14.3
**Status:** The recorded backend and frontend test suites pass. The production build remains under verification; no release-readiness or certification claim is made.

## Verified test results

| Suite | Command | Result |
|---|---|---|
| Backend | `python -m pytest backend/tests -q` | 196 passed, 8 skipped, 43 warnings |
| Engineering benchmarks | Run by `npm test` (`npx tsx src/testRunner.ts`) | 92 passed across 11 suites |
| Frontend Vitest | Run by `npm test` (`vitest run`) | 37 passed across 8 test files |

These are runner totals for the executions recorded on November 11, 2026. Passing tests do not constitute certification of every module, input range, or engineering use.

## Production build

The production build was attempted with output redirected to a temporary directory, including a retry with `ESBUILD_BINARY_PATH` set to the installed Windows esbuild executable.

- TypeScript checking completed, and Vite transformed 2,549 modules.
- The build command then failed with `remove C:\Users\rocel\AppData\Local\Temp\esbuild-<hash>: Access is denied`.
- Inspection of the temporary output after the failure found only `placeholder-logo.svg`; there was no `index.html` or `assets` directory. Therefore, a usable production bundle was **not** produced by that run.
- The error’s underlying cause (for example, transient Windows locking or security software) has not been established.

## Remaining verification

- Resolve the Windows esbuild temporary-file cleanup failure and produce a complete bundle.
- Verify the canonical installed desktop workflow, including GUI presentation and API-backed operation.
- Verify backend deployment and binding behavior for the desktop product.
