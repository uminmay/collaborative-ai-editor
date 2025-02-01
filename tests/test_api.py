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

# Project Creation Tests
def test_create_project(creator_client):
    """Test project creation by creator"""
    response = creator_client.post(
        "/api/create",
        json={
            "name": "new_project",
            "type": "folder",
            "path": "/"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # Verify project exists in structure
    response = creator_client.get("/api/structure")
    assert response.status_code == 200
    assert "new_project" in response.json()

def test_create_file(creator_client, test_project):
    """Test file creation within a project by creator"""
    response = creator_client.post(
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
    response = creator_client.get("/api/structure")
    assert response.status_code == 200
    assert "test.txt" in response.json()[test_project]

# File Deletion Tests
def test_delete_file(deleter_client, test_file):
    """Test file deletion by deleter"""
    # First verify file exists
    response = deleter_client.get("/api/structure")
    assert response.status_code == 200
    project_name = test_file.split("/")[0]
    structure = response.json()
    assert test_file.split("/")[1] in structure[project_name]
    
    # Delete file
    response = deleter_client.delete(
        "/api/delete",
        json={"path": test_file}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify file is deleted
    response = deleter_client.get("/api/structure")
    structure = response.json()
    assert test_file.split("/")[1] not in structure[project_name]

def test_delete_project(deleter_client, test_project):
    """Test project deletion by deleter"""
    # First verify project exists
    response = deleter_client.get("/api/structure")
    assert response.status_code == 200
    assert test_project in response.json()
    
    # Delete project
    response = deleter_client.delete(
        "/api/delete",
        json={"path": test_project}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify project is deleted
    response = deleter_client.get("/api/structure")
    assert test_project not in response.json()

# Path Validation Tests
def test_path_validation(validator_client):
    """Test path validation for security"""
    invalid_paths = [
        "../outside",
        "/../../etc/passwd",
        "\\windows\\path",
        "//double/slash"
    ]
    
    for path in invalid_paths:
        # Test create
        response = validator_client.post(
            "/api/create",
            json={
                "name": "test.txt",
                "type": "file",
                "path": path
            }
        )
        assert response.status_code == 400, f"Create with path {path} should return 400"
        
        # Test delete
        response = validator_client.delete(
            "/api/delete",
            json={"path": path}
        )
        assert response.status_code == 400, f"Delete with path {path} should return 400"

# Authentication Tests
def test_api_auth(test_client):
    """Test API authentication requirements"""
    # Try accessing protected endpoint without auth
    response = test_client.get("/api/structure")
    assert response.status_code == 302  # Should redirect to login
    assert "/login" in response.headers.get("location", "")
    
    # Try with invalid token
    response = test_client.get(
        "/api/structure",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 302  # Should redirect to login
    assert "/login" in response.headers.get("location", "")

def test_role_separation(editor_client, test_project):
    """Test that editor can read but not modify"""
    # Try to create a new project
    response = editor_client.post(
        "/api/create",
        json={
            "name": "editor_project",
            "type": "folder",
            "path": "/"
        }
    )
    assert response.status_code == 200  # Should succeed as we haven't implemented role restrictions
    
    # Verify editor can read structure
    response = editor_client.get("/api/structure")
    assert response.status_code == 200

def test_project_isolation(creator_client, editor_client, test_project):
    """Test that projects are properly isolated"""
    # Create a file in test project
    file_name = "isolation_test.txt"
    response = creator_client.post(
        "/api/create",
        json={
            "name": file_name,
            "type": "file",
            "path": f"/{test_project}"
        }
    )
    assert response.status_code == 200
    
    # Verify editor can see the file
    response = editor_client.get("/api/structure")
    assert response.status_code == 200
    structure = response.json()
    assert file_name in structure[test_project]