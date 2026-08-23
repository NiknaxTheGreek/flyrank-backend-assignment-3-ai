# FlyRank Backend Assignment 3

Assignment 3 keeps the **final Assignment 2 service, routes, request bodies, response shapes, status codes, validation behavior, error JSON, path-ID behavior, and task fields unchanged**. The only implementation difference is the repository/storage layer: Assignment 2's SQLite repository is replaced by a PostgreSQL repository running in Docker Compose.

Docker Compose starts the FastAPI `api` service and PostgreSQL `db` service, waits for database health, creates or migrates the `tasks` table, and seeds the exact Assignment 2 starter tasks only when the table is empty.

## Current verification status

- **Assignment 2 compatibility suite: PASS** — 10 local tests passed on the corrected code.
- **Python compilation, Compose configuration, verifier shell syntax, and whitespace checks: PASS.**
- **Live Docker persistence verifier: not completed in Replit** — the revised image built, but this host marked PostgreSQL unhealthy before the API could start. The exact output and boundary are recorded in [`VERIFICATION_EVIDENCE.md`](VERIFICATION_EVIDENCE.md).

## Unchanged Assignment 2 API contract

| Method | Path | Result |
| --- | --- | --- |
| `GET` | `/` | `200` with `{"name":"Task API","version":"1.0","endpoints":["/tasks"]}` |
| `GET` | `/health` | `200` with `{"status":"ok"}` |
| `GET` | `/tasks` | `200` with tasks shaped as `id`, nullable `title`, and nullable `done` |
| `POST` | `/tasks` | `201`; body accepts only a non-blank `title` and creates `done: false` |
| `GET` | `/tasks/{task_id}` | `200`, or `404` with `{"error":"Task {id} not found"}` |
| `PUT` | `/tasks/{task_id}` | `200`; partial `title`/`done` update, or the Assignment 2 `400`/`404` JSON errors |
| `DELETE` | `/tasks/{task_id}` | `204` with an empty body, or the Assignment 2 `404` JSON error |

Malformed request bodies, unsupported fields, and malformed numeric IDs return `400` with `{"error":"Invalid request body"}`. An empty update body returns `400` with `{"error":"Request body must include title and/or done"}`.

## Run with Docker

```bash
cp .env.example .env
docker compose up --build
```

`.env` is gitignored. `DATABASE_URL` is required and must point at the Compose `db` host; `.env.example` contains a safe development value. The PostgreSQL user, password, database name, connection string, and API port are all required from `.env`.

Open `http://localhost:8000/docs` after startup.

Stop the stack without erasing data:

```bash
docker compose down
```

Use `docker compose down -v` only when deliberately removing the named PostgreSQL volume.

## Verification and persistence

Run the deterministic Assignment 2 compatibility and static checks:

```bash
python -m pytest backend/tests -q
```

On a Docker-capable runner, execute:

```bash
./scripts/verify_docker_runtime.sh
```

The verifier starts a fresh Compose stack, performs live Assignment 2-compatible CRUD, confirms stored state directly with `psql`, then runs `docker compose down` followed by `docker compose up` without `-v`. That recreates both the API and database containers while retaining the named PostgreSQL volume, and confirms the created task remains available. Historical external evidence for this architecture and the current Replit limitation are documented separately in [`VERIFICATION_EVIDENCE.md`](VERIFICATION_EVIDENCE.md).

## Deliverable evidence

- [`REQUIREMENTS_AUDIT.md`](REQUIREMENTS_AUDIT.md) maps the compatibility, Docker, and PostgreSQL requirements to implementation and evidence.
- [`VERIFICATION_EVIDENCE.md`](VERIFICATION_EVIDENCE.md) records only actual local checks, the current Docker outcome, and clearly scoped historical external evidence.