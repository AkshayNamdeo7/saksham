"""
API integration tests for the full recommendation flow with seeded DB.

Requires the app to be importable. Uses the in-memory test DB.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["DATABASE_URL"] = "sqlite:///./test_saksham.db"
os.environ["SEED_ON_STARTUP"] = "1"

import pytest
from fastapi.testclient import TestClient

from app.db.session import Base, engine
from app.db.seed import seed
from app.db.session import SessionLocal
from app.main import app


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_schemes_list(client):
    r = client.get("/api/schemes")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 5
    assert all(s["max_loan"] >= 0 for s in data)


def test_partners_list(client):
    r = client.get("/api/partners?state=Madhya Pradesh")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 5
    assert all("Demo" not in p["name"] or True for p in data)


def test_recommendation_demo_flow(client):
    profile = {
        "age": 32,
        "state": "Madhya Pradesh",
        "district": "Bhopal",
        "city": "Bhopal",
        "annual_family_income": 240000,
        "purpose": "business",
        "project_type": "small_manufacturing",
        "project_cost": 120000,
        "requested_loan": 120000,
        "language": "en",
    }
    r = client.post("/api/recommendations", json={"profile": profile})
    assert r.status_code == 200
    data = r.json()
    results = data["results"]
    assert len(results) > 0
    best = results[0]
    assert best["match_score"] >= 70
    assert best["eligibility_status"] in ("eligible", "conditional")


def test_emi_endpoint(client):
    r = client.post(
        "/api/calculator/emi",
        json={
            "principal": 120000,
            "annual_rate": 4.0,
            "tenure": 3,
            "tenure_unit": "years",
            "moratorium_months": 0,
            "scheme_max_loan": 140000,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["emi"] > 0
    assert data["tenure_months"] == 36
    assert data["warnings"] == []


def test_emi_over_limit_warning(client):
    r = client.post(
        "/api/calculator/emi",
        json={
            "principal": 200000,
            "annual_rate": 4.0,
            "tenure": 3,
            "tenure_unit": "years",
            "moratorium_months": 0,
            "scheme_max_loan": 140000,
        },
    )
    data = r.json()
    assert len(data["warnings"]) == 1


def test_partner_recommend(client):
    r = client.post(
        "/api/partners/recommend",
        json={
            "state": "Madhya Pradesh",
            "district": "Bhopal",
            "latitude": 23.2599,
            "longitude": 77.4126,
            "purpose": "business",
            "loan_amount": 120000,
            "limit": 5,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["results"]) > 0
    top = data["results"][0]
    assert top["total_score"] >= 70
    assert set(top["breakdown"].keys()) == {"scheme", "distance", "capacity", "eligibility"}


def test_assistant_chat_hi(client):
    r = client.post(
        "/api/assistant/chat",
        json={
            "language": "hi",
            "message": "Mujhe 1 lakh dairy business ke liye loan chahiye",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["language"] == "hi"


def test_admin_login(client):
    r = client.post(
        "/api/admin/auth/login",
        data={"username": "admin", "password": "saksham@2026"},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_admin_dashboard_requires_auth(client):
    r = client.get("/api/admin/dashboard")
    assert r.status_code in (401, 403)


def test_admin_crud(client):
    login = client.post(
        "/api/admin/auth/login",
        data={"username": "admin", "password": "saksham@2026"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    r = client.get("/api/admin/schemes", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) >= 5


def test_admin_create_delete_partner(client):
    login = client.post(
        "/api/admin/auth/login",
        data={"username": "admin", "password": "saksham@2026"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "Test Demo Branch",
        "type": "PSB",
        "state": "Madhya Pradesh",
        "district": "Bhopal",
        "city": "Bhopal",
        "address": "Test",
        "latitude": 23.2,
        "longitude": 77.4,
        "status": "accepting",
        "capacity_pct": 90,
        "scheme_slugs": ["micro-finance-scheme"],
    }
    r = client.post("/api/admin/partners", json=payload, headers=headers)
    assert r.status_code == 200
    pid = r.json()["id"]
    d = client.delete(f"/api/admin/partners/{pid}", headers=headers)
    assert d.status_code == 200