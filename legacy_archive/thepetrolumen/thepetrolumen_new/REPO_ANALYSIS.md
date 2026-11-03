# Repository Analysis — PetroLúmen

Summary
-------
- **Stack:** Python (FastAPI) backend + Next.js (Tauri) frontend. See [backend/README.md](backend/README.md) and [petrolumen/package.json](petrolumen/package.json).
- **CI:** Backend CI present ([.github/workflows/backend-ci.yml](.github/workflows/backend-ci.yml)), frontend CI not found.

Key Findings
------------
- **Secrets & defaults (HIGH):** Default/placeholder secrets in [backend/config.py](backend/config.py) and [backend/.env.example](backend/.env.example). `config.py` prints `SECRET_KEY` when run and `main.py` creates a default admin account (`admin/adminpassword`) on startup. These are high-risk for production.
- **Hardcoded test secrets:** Test fixtures and examples include test secret keys and passwords (e.g., `tests/conftest.py`, `removed_content_example/example_conftest.py`).
- **Global state / concurrency risk:** `res_simulator` (FlowSimulation) is instantiated as a global in [backend/main.py](backend/main.py), which is stateful and may be unsafe for concurrent requests.
- **Dependencies:** Backend pinned in [backend/requirements.txt](backend/requirements.txt) (FastAPI, Pydantic, SQLAlchemy, NumPy, SciPy, etc.). Frontend uses Next 15 + React 19 in [petrolumen/package.json](petrolumen/package.json).
- **TODOs & docs:** Many TODOs across backend and frontend (e.g., [backend/main.py](backend/main.py#L439), [petrolumen/app/page.tsx](petrolumen/app/page.tsx#L46)). Sphinx `todo` extension is enabled in `backend/docs_sphinx/conf.py`.
- **CI & tests:** Backend CI runs lint/black/pytest; frontend tests exist (`vitest`) but no CI workflow detected.

Immediate Recommendations (prioritized)
-------------------------------------
1. **Remove/guard default admin creation** — stop creating `admin/adminpassword` on startup. Gate behind a dev-only env var like `CREATE_DEV_ADMIN=true` or remove entirely. See [backend/main.py](backend/main.py#L1560-L1620).
2. **Stop printing secrets and clear defaults** — remove `print(SECRET_KEY)` and similar debug prints from [backend/config.py](backend/config.py). Require `SECRET_KEY` to be set (fail startup or warn loudly if default).
3. **Prevent committing secrets** — add pre-commit hooks and a CI step using `detect-secrets`/`gitleaks` or GitHub secret scanning. Enable scanning in [.github/workflows/backend-ci.yml](.github/workflows/backend-ci.yml).
4. **Treat test secrets carefully** — remove or parameterize hardcoded test secrets; use fixtures that derive secrets from environment or pytest config and ensure tests mark sensitive values.
5. **Fix global state** — refactor `res_simulator` into per-request/session objects or a managed pool to avoid concurrency bugs ([backend/main.py](backend/main.py#L120-L160)).
6. **Add frontend CI & dependency audit** — add GitHub Actions workflow to run `npm ci`, `npm run build`, `npm run test` and a dependency audit step (npm audit or GH Dependabot).
7. **Dependency & security audit** — run `pip-audit`, `safety`, or GitHub Dependabot for Python packages; upgrade critical vulnerabilities.

Next steps I can take for you
----------------------------
- Open a PR that: (a) removes default admin creation and guards it with an env var, (b) removes secret printing in `config.py`, and (c) adds a simple `gitleaks` check to the backend CI. Tell me which items you'd like prioritized and I will implement them.

Files reviewed (representative)
- [backend/config.py](backend/config.py)
- [backend/main.py](backend/main.py)
- [backend/requirements.txt](backend/requirements.txt)
- [backend/.env.example](backend/.env.example)
- [backend/tests/](backend/tests/)
- [petrolumen/package.json](petrolumen/package.json)
- [.github/workflows/backend-ci.yml](.github/workflows/backend-ci.yml)

If you want, I can also:
- Run a dependency vulnerability scan and produce an upgrade plan.
- Create the PR with the quick security fixes above.

— End of analysis
