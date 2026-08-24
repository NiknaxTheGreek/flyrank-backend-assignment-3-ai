# FlyRank Backend Assignment 3

Assignment 3 keeps the **final Assignment 2 service, routes, request bodies, response shapes, status codes, validation behavior, error JSON, path-ID behavior, and task fields unchanged**. The implementation change is the storage/infrastructure layer: Assignment 2's SQLite repository is replaced by PostgreSQL running with the API in Docker Compose.

Docker Compose starts the FastAPI `api` service and PostgreSQL `db` service, waits for database health, creates the `tasks` table, and seeds the exact starter tasks only when the table is empty.

## Verification status

**Current Assignment 3 code passes the Docker/PostgreSQL runtime gate.**

GitHub Actions run `32700227130` verified:

- 10/10 regression/static tests pass;
- Docker and Docker Compose are available;
- PostgreSQL reaches healthy state;
- API starts against PostgreSQL;
- exactly three seed tasks exist;
- live API create/read/update succeeds;
- the created row is visible directly through `psql`;
- `docker compose down` is executed without `-v`;
- the stack is recreated;
- the created and updated task remains after restart.

The verifier finished with `Docker runtime verification passed.` See [`VERIFICATION_EVIDENCE.md`](VERIFICATION_EVIDENCE.md) and [`evidence/github-actions-docker-postgres-current.txt`](evidence/github-actions-docker-postgres-current.txt).

## Unchanged Assignment 2 API contract

| Method | Path | Result |
| --- | --- | --- |
| `GET` | `/` | `200` with API metadata |
| `GET` | `/health` | `200` with `{"status":"ok"}` |
| `GET` | `/tasks` | `200` with all tasks |
| `POST` | `/tasks` | `201`; valid non-blank title creates `done: false` |
| `GET` | `/tasks/{task_id}` | `200`, or `404` JSON error |
| `PUT` | `/tasks/{task_id}` | `200`; partial `title`/`done` update, or the Assignment 2 `400`/`404` behavior |
| `DELETE` | `/tasks/{task_id}` | `204` empty body, or `404` JSON error |

Malformed request bodies, unsupported fields, and malformed numeric IDs retain the final Assignment 2 validation/error behavior.

## Run with Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

`.env` is gitignored. `.env.example` contains safe development placeholders. The application connection string uses the Compose database service hostname `db`, not host-machine `localhost`.

Open `http://localhost:8000/docs` after startup.

Stop the stack without erasing data:

```bash
docker compose down
```

Use `docker compose down -v` only when deliberately deleting the named PostgreSQL volume.

## Verify

Run the compatibility/static suite:

```bash
python -m pytest backend/tests -q
```

On a Docker-capable machine or runner:

```bash
bash scripts/verify_docker_runtime.sh
```

The verifier creates an isolated Compose project, verifies seed count and live CRUD, checks the created row directly with PostgreSQL `psql`, brings the stack down without deleting its named volume, recreates it, and verifies the task remains.

The same verifier is executed automatically by `.github/workflows/docker-runtime.yml`.

## Evidence and audit

- [`REQUIREMENTS_AUDIT.md`](REQUIREMENTS_AUDIT.md) maps the S3 requirements to the implementation and current evidence.
- [`VERIFICATION_EVIDENCE.md`](VERIFICATION_EVIDENCE.md) records the current passing checkpoint and the earlier Replit limitation separately.
- [`evidence/github-actions-docker-postgres-current.txt`](evidence/github-actions-docker-postgres-current.txt) records the observed successful GitHub Actions result.

An earlier Replit attempt could not complete because that host marked PostgreSQL unhealthy. That failed environment attempt is retained only as historical evidence and does not supersede the current successful Docker-capable GitHub Actions run.
