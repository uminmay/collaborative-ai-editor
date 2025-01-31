import pytest
import os
import sys
from fastapi.testclient import TestClient

# Add the parent directory to PYTHONPATH
sys.path.append(os.path.abspath('./app'))

@pytest.fixture
def test_app():
    from app.main import app
    return app

@pytest.fixture
def test_client(test_app):
    return TestClient(test_app)

@pytest.fixture
def async_client(test_app):
    from httpx import AsyncClient
    return AsyncClient(app=test_app, base_url="http://test")