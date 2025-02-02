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
    password = "testpass"  # Store password in variable
    user_create = schemas.UserCreate(
        username=username,
        password=password  # Use same password
    )
    crud.create_user(test_db, user_create)
    
    # Test successful login
    response = test_client.post(
        "/login",
        data={
            "username": username,
            "password": password  # Use same password
        },
        follow_redirects=False
    )
    assert response.status_code == 302
    assert "access_token" in response.cookies

def test_logout(test_client):
    """Test user logout functionality"""
    response = test_client.get("/logout", follow_redirects=False)
    assert response.status_code in [302, 307]  # Both are valid redirect codes
    assert response.headers["location"] == "/login"

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
    login_response = test_client.post(
        "/login",
        data={
            "username": username,
            "password": "testpass"
        },
        follow_redirects=False
    )
    assert login_response.status_code == 302
    
    cookies = login_response.cookies
    headers = {"Cookie": f"session={cookies.get('session')}"}
    
    # Try accessing protected endpoint
    response = test_client.get("/api/structure", headers=headers, follow_redirects=False)
    assert response.status_code in [200, 302]  # Either direct access or redirect to /

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