import os
import sys
import pytest

# Add the parent directory to PYTHONPATH
sys.path.append(os.path.abspath('./app'))

@pytest.fixture
def test_app():
    from app.main import app
    return app

@pytest.fixture
def test_client(test_app):
    from fastapi.testclient import TestClient
    return TestClient(test_app)
