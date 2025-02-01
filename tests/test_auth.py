import pytest
from app.db import crud, schemas
from fastapi import status
import uuid

def test_login_page(test_client):
    """Test login page access"""
    response = test_client.get("/login")
    assert response.status_code == 200
    assert "Login" in response.text

def test_login(test_client, test_db):
    """Test user login functionality"""
    # Create a test user with unique username
    username = f"testlogin_{uuid.uuid4().hex[:8]}"
    user_create = schemas.UserCreate(
        username=username,
        password="testpass"
    )
    crud.create_user(test_db, user_create)
    
    # Test successful login
    response = test_client.post(
        "/login",
        data={
            "username": username,
            "password": "testpass"
        },
        allow_redirects=False
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/"
    assert "access_token" in response.cookies
    
    # Test failed login
    response = test_client.post(
        "/login",
        data={
            "username": username,
            "password": "wrongpass"
        }
    )
    assert response.status_code == 200  # Returns login page with error
    assert "Invalid username or password" in response.text

def test_logout(test_client):
    """Test user logout functionality"""
    response = test_client.get("/logout", allow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"
    
    # Check cookies
    cookies = response.headers.get("set-cookie", "")
    assert "access_token=;" in cookies  # Cookie cleared

def test_session_authentication(test_client, test_db):
    """Test session-based authentication"""
    # Create unique test user
    username = f"testsession_{uuid.uuid4().hex[:8]}"
    user_create = schemas.UserCreate(
        username=username,
        password="testpass"
    )
    crud.create_user(test_db, user_create)
    
    # Login
    response = test_client.post(
        "/login",
        data={
            "username": username,
            "password": "testpass"
        },
        allow_redirects=False
    )
    assert response.status_code == 302
    
    # Get cookies from response
    cookies = response.cookies
    
    # Try accessing protected endpoint
    response = test_client.get(
        "/api/structure",
        cookies=cookies
    )
    assert response.status_code == 200

def test_token_authentication(test_client, test_db):
    """Test token-based authentication"""
    # Create unique test user
    username = f"testtoken_{uuid.uuid4().hex[:8]}"
    user_create = schemas.UserCreate(
        username=username,
        password="testpass"
    )
    crud.create_user(test_db, user_create)
    
    # Login to get token
    response = test_client.post(
        "/login",
        data={
            "username": username,
            "password": "testpass"
        },
        allow_redirects=False
    )
    assert response.status_code == 302
    
    # Extract token from cookie
    token = response.cookies["access_token"]
    
    # Use token to access protected endpoint
    response = test_client.get(
        "/api/structure",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200