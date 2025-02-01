# tests/test_api.py
import pytest
from fastapi import status
import json
import os
from pathlib import Path
import shutil

def setup_module(module):
    """Setup test environment before module execution"""
    Path("editor_files").mkdir(exist_ok=True)

def teardown_module(module):
    """Cleanup after module execution"""
    shutil.rmtree("editor_files", ignore_errors=True)

def test_create_project(authenticated_client):
    """Test project creation"""
    response = authenticated_client.post(
        "/api/create",
        json={
            "name": "new_project",
            "type": "folder",
            "path": "/"
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify project exists in structure
    response = authenticated_client.get("/api/structure")
    assert response.status_code == 200
    assert "new_project" in response.json()

def test_create_file(authenticated_client, test_project):
    """Test file creation within a project"""
    response = authenticated_client.post(
        "/api/create",
        json={
            "name": "test.txt",
            "type": "file",
            "path": f"/{test_project}"
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify file exists in structure
    response = authenticated_client.get("/api/structure")
    assert response.status_code == 200
    assert "test.txt" in response.json()[test_project]

def test_delete_file(authenticated_client, test_file):
    """Test file deletion"""
    response = authenticated_client.request(
        "DELETE",
        "/api/delete",
        json={"path": test_file}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify file is gone from structure
    response = authenticated_client.get("/api/structure")
    project_name = test_file.split("/")[0]
    assert response.status_code == 200
    assert "test_file.txt" not in response.json()[project_name]

def test_delete_project(authenticated_client, test_project):
    """Test project deletion"""
    response = authenticated_client.request(
        "DELETE",
        "/api/delete",
        json={"path": test_project}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify project is gone from structure
    response = authenticated_client.get("/api/structure")
    assert response.status_code == 200
    assert test_project not in response.json()

def test_path_validation(authenticated_client):
    """Test path validation for security"""
    invalid_paths = [
        "../outside",
        "/../../etc/passwd",
        "\\windows\\path",
        "//double/slash"
    ]
    
    for path in invalid_paths:
        # Test create
        response = authenticated_client.post(
            "/api/create",
            json={
                "name": "test.txt",
                "type": "file",
                "path": path
            }
        )
        assert response.status_code == 400, f"Create with path {path} should return 400"
        
        # Test delete
        response = authenticated_client.request(
            "DELETE",
            "/api/delete",
            json={"path": path}
        )
        assert response.status_code == 400, f"Delete with path {path} should return 400"

def test_api_auth(test_client):
    """Test API authentication"""
    # Try accessing protected endpoint without auth
    response = test_client.get("/api/structure")
    assert response.status_code == 401
    
    # Try with invalid token
    response = test_client.get(
        "/api/structure",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401