"""Tests for Authentication and Rate Limiting Middleware."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_auth_register_and_login_flow():
    # 1. Register new user
    email = "trader_test_2026@tradly.ai"
    password = "SecurePassword2026!"
    name = "Test Trader"

    res_reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "name": name},
    )
    assert res_reg.status_code in [200, 409]

    # 2. Login with credentials
    res_login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res_login.status_code == 200
    data = res_login.json()["data"]
    assert "access_token" in data
    assert data["user"]["email"] == email
    token = data["access_token"]

    # 3. Access protected /me profile endpoint
    res_me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_me.status_code == 200
    assert res_me.json()["data"]["email"] == email


def test_auth_invalid_password():
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "demo@tradly.ai", "password": "WrongPassword123!"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHENTICATED"


def test_rate_limit_headers():
    res = client.get("/api/v1/market/pairs")
    assert res.status_code == 200
    assert "X-RateLimit-Limit" in res.headers
    assert "X-RateLimit-Remaining" in res.headers
    assert "X-RateLimit-Reset" in res.headers
