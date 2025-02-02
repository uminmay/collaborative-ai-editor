import pytest
import uuid
from app.db import crud, schemas

def test_login_page(test_client):
    """Test login page access"""
    response = test_client.get("/login")
    assert response.status_code == 200
    assert "Login" in response.text

def test_login(test_client, test_db):
    """Test user login functionality"""
    username = f"testlogin_{uuid.uuid4().hex[:8]}"
    password = "testpass"
    # Create a test user
    user_create = schemas.UserCreate(
        username=username,
        password=password
    )
    user = crud.create_user(test_db, user_create)
    assert user is not None
    
    response = test_client.post(
        "/login",
        data={
            "username": username,
            "password": password
        },
        follow_redirects=False
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/"
    assert "access_token" in response.cookies

def test_logout(test_client):
    """Test user logout functionality"""
    response = test_client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"
    assert not response.cookies.get("access_token")  # Cookie should be cleared

def test_session_authentication(test_client, test_db):
    """Test session-based authentication"""
    username = f"testsession_{uuid.uuid4().hex[:8]}"
    password = "testpass"
    user_create = schemas.UserCreate(
        username=username,
        password=password
    )
    user = crud.create_user(test_db, user_create)
    assert user is not None
    
    # Login to create session
    login_response = test_client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False
    )
    assert login_response.status_code == 302
    
    # Test protected endpoint access
    cookies = login_response.cookies
    response = test_client.get("/api/structure", cookies=cookies)
    assert response.status_code == 200

def test_token_authentication(test_client, test_db):
    """Test token-based authentication"""
    username = f"testtoken_{uuid.uuid4().hex[:8]}"
    password = "testpass"
    user_create = schemas.UserCreate(
        username=username,
        password=password
    )
    user = crud.create_user(test_db, user_create)
    assert user is not None
    
    login_response = test_client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False
    )
    assert login_response.status_code == 302
    assert "access_token" in login_response.cookies

    # Test with auth token
    token = login_response.cookies["access_token"]
    response = test_client.get(
        "/api/structure",
        headers={"Authorization": token}
    )
    assert response.status_code == 200