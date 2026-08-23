from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.repository import InMemoryTaskRepository


@pytest.fixture
def repository() -> InMemoryTaskRepository:
    return InMemoryTaskRepository()


@pytest.fixture
def client(repository: InMemoryTaskRepository) -> Iterator[TestClient]:
    with TestClient(create_app(repository)) as test_client:
        yield test_client