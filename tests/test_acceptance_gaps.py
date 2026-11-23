"""Acceptance-gap tests for eligible applications and listing publication."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.seed import seed

client = TestClient(app)
PASSWORDS = {
    "admin@example.com": "admin-dev",
    "grad.dcit@example.com": "grad-dev",
    "grad.other@example.com": "grad-dev",
    "employer@example.com": "employer-dev",
}


@pytest.fixture(autouse=True)
def fresh_db():
    seed(reset=True)
    yield


def uid(email: str) -> int:
    response = client.post("/api/auth/login", json={"email": email, "password": PASSWORDS[email]})
    assert response.status_code == 200
    return response.json()["user"]["id"]


def test_non_dcit_graduate_cannot_subscribe():
    response = client.post("/api/graduates/subscribe", json={"actor_id": uid("grad.other@example.com")})
    assert response.status_code == 400


def test_non_dcit_graduate_cannot_apply():
    response = client.post("/api/graduates/applications", json={
        "listing_id": 1,
        "cover_letter": "Not eligible",
        "actor_id": uid("grad.other@example.com"),
    })
    assert response.status_code == 400


def test_employer_submission_starts_pending():
    response = client.post("/api/employer/listings", json={
        "title": "New role",
        "company": "Acme",
        "description": "Build things",
        "apply_mode": "collect",
        "deadline": "2099-12-31",
        "actor_id": uid("employer@example.com"),
    })
    assert response.status_code == 200
    assert response.json()["status"] == "pending"


def test_external_expired_and_pending_listings_do_not_accept_applications():
    dcit_id = uid("grad.dcit@example.com")
    for listing_id in (2, 3):
        response = client.post("/api/graduates/applications", json={
            "listing_id": listing_id,
            "cover_letter": "Application",
            "actor_id": dcit_id,
        })
        assert response.status_code == 400


def test_publishing_notifies_subscribers():
    response = client.post("/api/admin/listings/2/publish", json={"actor_id": uid("admin@example.com")})
    assert response.status_code == 200
    assert response.json()["notified"] is True
    assert response.json()["count"] >= 1


def test_graduate_listing_view_excludes_pending_and_expired_jobs():
    response = client.get("/api/jobs")
    assert response.status_code == 200
    ids = {listing["id"] for listing in response.json()["jobs"]}
    assert 1 in ids
    assert 2 not in ids
    assert 3 not in ids
