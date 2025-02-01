import pytest
from fastapi import status
import json
import os

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
    response = authenticated_client.delete(
        "/api/delete",
        headers={"Content-Type": "application/json"},
        content=json.dumps({"path": test_file})
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
    response = authenticated_client.delete(
        "/api/delete",
        headers={"Content-Type": "application/json"},
        content=json.dumps({"path": test_project})
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify project is gone from structure
    response = authenticated_client.get("/api/structure")
    assert response.status_code == 200
    assert test_project not in response.json()

def test_get_structure(authenticated_client, test_project):
    """Test getting project structure"""
    # Create some nested files
    authenticated_client.post(
        "/api/create",
        json={
            "name": "subfolder",
            "type": "folder",
            "path": f"/{test_project}"
        }
    )
    authenticated_client.post(
        "/api/create",
        json={
            "name": "test.txt",
            "type": "file",
            "path": f"/{test_project}/subfolder"
        }
    )
    
    response = authenticated_client.get("/api/structure")
    assert response.status_code == 200
    structure = response.json()
    
    # Verify structure
    assert test_project in structure
    assert "subfolder" in structure[test_project]
    assert "test.txt" in structure[test_project]["subfolder"]

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
        assert response.status_code == 400
        
        # Test delete
        response = authenticated_client.delete(
            "/api/delete",
            headers={"Content-Type": "application/json"},
            content=json.dumps({"path": path})
        )
        assert response.status_code == 400