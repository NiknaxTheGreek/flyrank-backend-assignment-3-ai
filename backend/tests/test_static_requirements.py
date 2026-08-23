from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_compose_declares_healthy_postgres_and_named_volume() -> None:
    compose = (PROJECT_ROOT / "docker-compose.yml").read_text()

    assert "postgres:16-alpine" in compose
    assert "pg_isready" in compose
    assert "condition: service_healthy" in compose
    assert "flyrank_postgres_data:" in compose
    assert "env_file:" in compose
    assert "${APP_ENV_FILE:-.env}" in compose
    assert "DATABASE_URL:-" not in compose


def test_docker_and_hygiene_files_are_present() -> None:
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text()

    assert "python:3.13-slim" in dockerfile
    assert "uvicorn" in dockerfile
    for filename in (".env.example", ".gitignore", ".dockerignore"):
        assert (PROJECT_ROOT / filename).is_file()
    assert ".env" in (PROJECT_ROOT / ".gitignore").read_text().splitlines()
    env_example = (PROJECT_ROOT / ".env.example").read_text()
    assert "DATABASE_URL=postgresql://" in env_example


def test_production_repository_uses_parameterized_sql_and_idempotent_seed() -> None:
    repository = (PROJECT_ROOT / "backend" / "app" / "repository.py").read_text()

    assert "VALUES (%s, %s)" in repository
    assert "WHERE id = %s" in repository
    assert "SELECT COUNT(*) AS task_count FROM tasks" in repository
    assert "if row and row[\"task_count\"] == 0" in repository
    assert "LOCK TABLE tasks" in repository
    assert "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS done BOOLEAN" in repository


def test_external_docker_runtime_proof_is_committed() -> None:
    script = PROJECT_ROOT / "scripts" / "verify_docker_runtime.sh"
    workflow = PROJECT_ROOT / ".github" / "workflows" / "docker-runtime.yml"

    assert script.is_file()
    assert workflow.is_file()
    contents = script.read_text()
    assert "docker compose" in contents
    assert "psql" in contents
    assert "down" in contents
    assert "up" in contents
    assert "  env" in contents
    assert "  -u DATABASE_URL" in contents