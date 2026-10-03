import os

# Keep the developer's local .env, which may hold an API key, out of tests.
os.environ["TINYDESK_LOAD_DOTENV"] = "0"

import pytest
from fastapi.testclient import TestClient

from backend.app import app


@pytest.fixture
def client():
    app.dependency_overrides.clear()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
