import pytest
from fastapi.testclient import TestClient

from alertforge.api.app import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
