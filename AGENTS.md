# Repository Guidelines

## Project Structure & Module Organization
Backend FastAPI lives under `backend/` with handlers in `routers/`, shared logic in `services/`, and migrations in `migration/`. The React + TypeScript client sits in `frontend/src/`; create feature views in `pages/`, share UI in `components/`, and keep static assets in `public/`. Automation scripts live in `agents/`, `scripts/`, and `chrome-extension/`; containers stay in `docker/`. Keep backend tests in `tests/` with frontend specs colocated next to their components (e.g., `MyWidget.test.tsx`).

## Build, Test, and Development Commands
Run the following workflows routinely:
- `./setup-env.sh` initializes a hardened `.env` and service secrets.
- `./start-backend` brings up Postgres, Redis, API, frontend, and nginx via Docker health checks.
- `cd backend && uvicorn main:app --reload` launches the API in dev mode against SQLite or your configured DB.
- `cd backend && python -m pytest tests/ -v --cov=. --cov-report=xml` keeps async suites green and refreshes `coverage.xml`.
- `cd frontend && npm install && npm run start` sets up the React dev server; use `npm run build` for production bundles and `npm test -- --coverage` before releases.

## Coding Style & Naming Conventions
Follow four-space indentation and full type hints for Python 3.11. Format the service with `black`, sort imports via `isort`, lint using `flake8`, and gate types with `mypy`. React code uses two-space indentation, PascalCase components, camelCase hooks, and SCSS modules. Keep configuration names uppercase (`SECRET_KEY`) and only version `.env.example`.

## Testing Guidelines
Maintain ≥85% backend coverage. Backend suites rely on built-in async fixtures and should avoid real service calls. Use React Testing Library for UI flows and keep snapshots stable. Run scenario scripts (`test-agent-coordination.py`, `test_ml_performance.py`, `security-validation.sh`) before promoting coordinated releases.

## Commit & Pull Request Guidelines
Adopt the house commit style: optional emoji prefix plus imperative summary under 72 characters (example: `✨ Add artifact import wizard`). Scope commits narrowly, bundling migrations and docs with schema changes and noting lint or test results in the body. Pull requests must link to issues, flag risk areas, summarize coverage impact, and attach screenshots or API examples for UX or interface tweaks.

## Security & Configuration Tips
Regenerate secrets via `./setup-env.sh` during rotations, keeping overrides in a local `.env`. After dependency or auth updates, run `security-validation.sh` to lint configs and scan CVEs. The Docker stack assumes TLS termination from `docker/nginx`; adjust `nginx.conf` instead of bypassing the proxy when exposing new endpoints.
