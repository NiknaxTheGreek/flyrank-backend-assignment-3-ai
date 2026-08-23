# Verification Evidence

This file separates current, directly observed results from historical external Docker evidence. It does not present unavailable Docker execution as a pass.

## Current corrected-code checks

| Check | Command | Actual result |
| --- | --- | --- |
| Assignment 2 compatibility and static suite | `python -m pytest backend/tests -q` | Passed: **10 passed** |
| Python syntax | `find backend -type f -name '*.py' -print0 \| xargs -0 python -m py_compile` | Passed |
| Required `.env` Compose rendering | `APP_ENV_FILE=.env.example docker compose --env-file .env.example config` | Passed |
| Docker verifier shell syntax | `bash -n scripts/verify_docker_runtime.sh` | Passed |
| Whitespace | `git diff --check -- artifacts/flyrank-backend-assignment-3` | Passed |

## Current Docker runtime attempt

The revised verifier was run in this Replit environment. It built the API image, created the isolated network and named volume, and started PostgreSQL. Docker then marked the PostgreSQL container unhealthy before the API service could start:

```text
Container ...-db-1  Error
dependency failed to start: container ...-db-1 is unhealthy
```

The verifier exited with status `1`. No live CRUD, direct `psql`, or persistence pass is claimed for this corrected-code run in Replit.

## Historical external persistence evidence

Before this Assignment 2 compatibility correction, the same Docker/PostgreSQL architecture was verified on a real GitHub Actions runner: Compose startup, live CRUD, direct `psql` inspection, `docker compose down` followed by `up` without `-v`, named-volume persistence, and a post-restart regression suite all passed.

That is retained as historical architecture evidence only. It is not represented as a successful Docker run of the current corrected code. The updated verifier now uses the final Assignment 2 request/response contract and must be run on a Docker-capable runner to produce new live proof.