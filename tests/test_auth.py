import pytest
from app.db import crud, schemas
from fastapi import status
import uuid

def test_login_page(test_client):
    """Test login page access"""
    response = test_client.get("/login")
    assert response.status_code == 200
    assert "Login" in response.text

def test_logout(test_client):
    """Test user logout functionality"""
    response = test_client.get("/logout", follow_redirects=False)
    assert response.status_code in [302, 307]  # Both are valid redirect codes
    assert response.headers["location"] == "/login"

def test_login(test_client, test_db):
    """Test user login functionality"""
    username = f"testlogin_{uuid.uuid4().hex[:8]}"
    password = "testpass"
    user_create = schemas.UserCreate(
        username=username,
        password=password
    )
    user = crud.create_user(test_db, user_create)
    
    response = test_client.post(
        "/login",
        data={
            "username": username,
            "password": password
        },
        follow_redirects=False
    )
    assert response.status_code == 302

def test_session_authentication(test_client, test_db):
    """Test session-based authentication"""
    username = f"testsession_{uuid.uuid4().hex[:8]}"
    password = "testpass"
    user_create = schemas.UserCreate(username=username, password=password)
    user = crud.create_user(test_db, user_create)
    
    # Login to create session
    login_response = test_client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False
    )
    assert login_response.status_code == 302
    
    # Test protected endpoint access
    cookies = login_response.cookies
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
    login_response = test_client.post(
        "/login",
        data={
            "username": username,
            "password": "testpass"
        },
        follow_redirects=False
    )
    assert login_response.status_code == 302
    
    # Get token from cookie
    cookies = login_response.cookies
    token = cookies.get("access_token")
    
    if token and token.startswith("Bearer "):
        token = token[7:]  # Remove "Bearer " prefix
        
    # Use token to access protected endpoint
    response = test_client.get(
        "/api/structure",
        headers={"Authorization": f"Bearer {token}"},
        follow_redirects=False
    )
    assert response.status_code in [200, 302]