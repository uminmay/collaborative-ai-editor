import pytest
from app.db import crud, schemas
from fastapi import status

def test_login(test_client, test_db):
    """Test user login functionality"""
    # Create a test user
    user_create = schemas.UserCreate(
        username="testlogin",
        password="testpass"
    )
    crud.create_user(test_db, user_create)
    
    # Test successful login
    response = test_client.post(
        "/login",
        data={
            "username": "testlogin",
            "password": "testpass"
        }
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/"
    
    # Test failed login
    response = test_client.post(
        "/login",
        data={
            "username": "testlogin",
            "password": "wrongpass"
        }
    )
    assert response.status_code == 200  # Returns login page with error
    assert "Invalid username or password" in response.text

def test_logout(test_client):
    """Test user logout functionality"""
    response = test_client.get("/logout")
    assert response.status_code == 302
    assert response.headers["location"] == "/login"
    
    # Verify access token cookie is cleared
    assert "access_token" not in response.cookies

def test_session_authentication(test_client, test_db):
    """Test session-based authentication"""
    # Create and login user
    user_create = schemas.UserCreate(
        username="testsession",
        password="testpass"
    )
    crud.create_user(test_db, user_create)
    
    login_response = test_client.post(
        "/login",
        data={
            "username": "testsession",
            "password": "testpass"
        }
    )
    assert login_response.status_code == 302
    
    # Access protected endpoint
    response = test_client.get("/api/structure")
    assert response.status_code == 200

def test_token_authentication(test_client, test_db):
    """Test token-based authentication"""
    # Create and login user
    user_create = schemas.UserCreate(
        username="testtoken",
        password="testpass"
    )
    crud.create_user(test_db, user_create)
    
    login_response = test_client.post(
        "/login",
        data={
            "username": "testtoken",
            "password": "testpass"
        }
    )
    assert login_response.status_code == 302
    
    # Extract token from cookie
    cookies = login_response.cookies
    assert "access_token" in cookies
    token = cookies["access_token"]
    
    # Use token to access protected endpoint
    response = test_client.get(
        "/api/structure",
        headers={"Authorization": token}
    )
    assert response.status_code == 200