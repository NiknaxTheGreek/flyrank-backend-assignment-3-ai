# Verification Evidence

This file records only executed checks and observed results for the current Assignment 3 code.

## Current-code verification

GitHub Actions run `32700227130` executed the current pull-request code on an Ubuntu 24.04 hosted runner using Python 3.13, Docker 28.0.4, and Docker Compose v2.38.2.

| Check | Actual result |
| --- | --- |
| Assignment 2 compatibility/static suite | **PASS — 10 passed** |
| Docker runtime available | **PASS** |
| PostgreSQL container health | **PASS — healthy** |
| API container startup | **PASS** |
| Exactly three starter tasks | **PASS** |
| Live API create/read/update | **PASS** |
| Direct PostgreSQL `psql` check | **PASS** |
| `docker compose down` without `-v` | **PASS** |
| Stack recreation | **PASS** |
| Named-volume persistence after restart | **PASS** |
| Workflow job | **PASS** |

The decisive verifier output ended with:

```text
Restarting without -v to prove named-volume persistence.
Docker runtime verification passed.
```

The committed transcript is [`evidence/github-actions-docker-postgres-current.txt`](evidence/github-actions-docker-postgres-current.txt).

The workflow also uploaded the `assignment-3-docker-runtime-gate` artifact (artifact ID `9510248506`) containing the Docker/Compose version record and runtime verifier output.

## What the runtime verifier proves

`scripts/verify_docker_runtime.sh` starts an isolated Compose project with a temporary safe environment file. It then:

1. starts the API and PostgreSQL services;
2. waits for the API health endpoint;
3. verifies exactly three seeded tasks;
4. creates a task through the API;
5. reads and updates that task through the API;
6. queries the same row directly with `psql`;
7. brings the stack down without deleting volumes;
8. recreates the stack;
9. verifies the created task still exists with the updated value.

The script cleans up its isolated test volume only after the persistence assertion has passed.

## Earlier Replit limitation

An earlier run in Replit built the image and created the network/volume, but that host marked PostgreSQL unhealthy before the API could start. That failed attempt remains historical environment evidence only and is no longer the current acceptance result.

The current GitHub Actions run above is the authoritative runtime checkpoint for the corrected code.
