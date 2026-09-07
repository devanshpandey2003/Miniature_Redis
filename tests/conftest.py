"""
Shared pytest fixtures. `TestClient` wraps the FastAPI app and lets tests
make requests without a real network socket -- fast, and no port
conflicts between test runs.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.store import store
from app.api.deps import get_aof_logger


@pytest.fixture(autouse=True)
def clean_store():
    """
    Reset the shared store AND wipe the on-disk AOF log before every test.
    Without clearing the AOF file too, a leftover log from a previous run
    (or manual testing) gets replayed into the store the next time the
    app's lifespan startup runs -- which is exactly what caused a failing
    test here originally. In-memory state and on-disk state both need
    resetting for tests to be truly isolated.
    """
    store._data.clear()
    store._expires.clear()
    get_aof_logger().clear()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
