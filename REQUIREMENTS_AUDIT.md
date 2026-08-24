# Requirements Audit

## Current status

- **Final Assignment 2 API compatibility: PASS** — current suite: 10 passed.
- **Required `.env` configuration and Compose/static checks: PASS.**
- **Current Docker/PostgreSQL runtime and persistence checkpoint: PASS** — GitHub Actions run `32700227130` executed the current code successfully.

| Requirement | Implementation | Current evidence | Status |
| --- | --- | --- | --- |
| Exact Assignment 2 root and health responses | Assignment 2-compatible FastAPI route layer | Compatibility suite | PASS |
| Exact Assignment 2 task shape and CRUD behavior | `id`, nullable `title`, nullable `done`; Assignment 2 request/error behavior | Compatibility suite | PASS |
| Only storage differs | Assignment 2-compatible routes use the PostgreSQL repository interface | Route/repository review and compatibility suite | PASS |
| PostgreSQL in Docker | Compose `db` service and API image | Current GitHub Actions runtime gate | PASS |
| One-command application/database startup | `docker compose up --build` | Current runtime gate and README | PASS |
| Persistent PostgreSQL volume | `flyrank_postgres_data` | Current down/up persistence checkpoint | PASS |
| Required gitignored connection string | `.env` ignored; `.env.example` includes required `DATABASE_URL`; Compose has no fallback | Static suite and Compose rendering | PASS |
| Compose service networking | API connection string uses database service hostname `db`, not host `localhost` | `.env.example`, Compose configuration, successful runtime gate | PASS |
| Table setup and seed-once behavior | PostgreSQL repository initialization creates the table and inserts exactly three starters only when empty | Static suite plus current runtime seed check | PASS |
| Parameterized SQL | Psycopg `%s` bindings | Static suite and repository review | PASS |
| Live CRUD against PostgreSQL | API create/read/update operations execute against Compose PostgreSQL | Current runtime gate | PASS |
| Direct database inspection | Verifier queries the created task directly with `psql` | Current runtime gate | PASS |
| Persistence across app/database restart | Verifier performs `docker compose down` without `-v`, recreates the stack, and asserts the created/updated task persists | Current runtime gate | PASS |
| Secret-safe repository | `.env` is ignored and safe placeholders are committed in `.env.example` | Repository review/static checks | PASS |
| README and evidence honesty | README/evidence distinguish the earlier failed Replit attempt from the current successful external run | Documentation review | PASS |

## Evidence

The authoritative current runtime evidence is recorded in:

- [`VERIFICATION_EVIDENCE.md`](VERIFICATION_EVIDENCE.md)
- [`evidence/github-actions-docker-postgres-current.txt`](evidence/github-actions-docker-postgres-current.txt)
- GitHub Actions workflow `.github/workflows/docker-runtime.yml`

The earlier Replit PostgreSQL-health failure remains historical environment evidence only; it is not the current acceptance result.
