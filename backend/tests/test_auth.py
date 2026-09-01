import pytest

def test_login_success(client):
    response = client.post("/api/v1/auth/login", json={
        "email": "teacher@facemark.demo",
        "password": "demo123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "teacher@facemark.demo"
    assert data["user"]["role"] == "TEACHER"

def test_login_invalid_password(client):
    response = client.post("/api/v1/auth/login", json={
        "email": "teacher@facemark.demo",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_login_nonexistent_user(client):
    response = client.post("/api/v1/auth/login", json={
        "email": "nobody@facemark.demo",
        "password": "demo"
    })
    assert response.status_code == 401

def test_get_me_authenticated(client, teacher_auth_headers):
    response = client.get("/api/v1/auth/me", headers=teacher_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "teacher@facemark.demo"
    assert data["full_name"] == "Teacher"

def test_get_me_unauthenticated(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
