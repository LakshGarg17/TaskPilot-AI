import pytest
from httpx import AsyncClient
from app.core.security import hash_password, verify_password

@pytest.mark.asyncio
async def test_password_hashing():
    pwd = "SecretPassword123!"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

@pytest.mark.asyncio
async def test_signup_and_cookie(client: AsyncClient):
    response = await client.post(
        "/api/auth/signup",
        json={"email": "pilot@example.com", "password": "securepassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "pilot@example.com"
    assert "id" in data
    # Check that cookie is set
    assert "access_token" in response.cookies

@pytest.mark.asyncio
async def test_signup_duplicate_email(client: AsyncClient):
    # First signup
    res1 = await client.post(
        "/api/auth/signup",
        json={"email": "duplicate@example.com", "password": "password123"}
    )
    assert res1.status_code == 200

    # Second signup with same email
    res2 = await client.post(
        "/api/auth/signup",
        json={"email": "duplicate@example.com", "password": "anotherpassword"}
    )
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]

@pytest.mark.asyncio
async def test_login_success_and_failure(client: AsyncClient):
    # Create user
    await client.post(
        "/api/auth/signup",
        json={"email": "user@example.com", "password": "mypassword"}
    )

    # Login with wrong password
    res_wrong = await client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "wrongpassword"}
    )
    assert res_wrong.status_code == 401
    assert "Incorrect email or password" in res_wrong.json()["detail"]

    # Login with correct password
    res_ok = await client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "mypassword"}
    )
    assert res_ok.status_code == 200
    data = res_ok.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "user@example.com"
    assert "access_token" in res_ok.cookies

@pytest.mark.asyncio
async def test_me_protected_route(client: AsyncClient):
    # Unauthenticated should fail
    res_unauth = await client.get("/api/auth/me")
    assert res_unauth.status_code == 401

    # Signup, which logs in and sets cookie
    signup_res = await client.post(
        "/api/auth/signup",
        json={"email": "authuser@example.com", "password": "mypassword"}
    )
    assert signup_res.status_code == 200

    # Test /me with cookie
    res_me = await client.get("/api/auth/me")
    assert res_me.status_code == 200
    assert res_me.json()["email"] == "authuser@example.com"

    # Logout
    logout_res = await client.post("/api/auth/logout")
    assert logout_res.status_code == 200

    # Now /me with empty cookie should fail
    client.cookies.clear()
    res_after_logout = await client.get("/api/auth/me")
    assert res_after_logout.status_code == 401
