"""Integration tests: lifecycle through the HTTP API (authorisation, 409, flags)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.seed import seed

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_db():
    seed(reset=True)
    yield


def uid(email):
    r = client.post("/api/auth/login", json={"email": email, "password": PASSWORDS[email]})
    return r.json()["user"]["id"]


PASSWORDS = {
    "admin@example.com": "admin-dev",
    "grad.dcit@example.com": "grad-dev",
    "employer@example.com": "employer-dev",
    "employer2@example.com": "employer-dev",
}


def new_application():
    """DCIT graduate applies to listing 1 (owned by employer@example.com)."""
    r = client.post(
        "/api/graduates/applications",
        json={"listing_id": 1, "cover_letter": "Hi", "actor_id": uid("grad.dcit@example.com")},
    )
    assert r.status_code == 200
    return r.json()["application_id"]


def act(app_id, actor_email, action):
    return client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": action, "actor_id": uid(actor_email)},
    )


def test_new_application_starts_submitted():
    aid = new_application()
    apps = client.get(
        "/api/graduates/applications", params={"actor_id": uid("grad.dcit@example.com")}
    ).json()["applications"]
    assert apps[0]["id"] == aid and apps[0]["status"] == "submitted"


def test_owner_can_walk_full_lifecycle():
    aid = new_application()
    for action, expected in [("mark_reviewed", "reviewed"), ("shortlist", "shortlisted"), ("hire", "hired")]:
        r = act(aid, "employer@example.com", action)
        assert r.status_code == 200
        assert r.json()["application"]["status"] == expected


def test_skipping_returns_409_and_leaves_status_unchanged():
    aid = new_application()
    for action in ("shortlist", "hire", "reject"):
        r = act(aid, "employer@example.com", action)
        assert r.status_code == 409
    apps = client.get(
        "/api/graduates/applications", params={"actor_id": uid("grad.dcit@example.com")}
    ).json()["applications"]
    assert apps[0]["status"] == "submitted"


@pytest.mark.parametrize("terminal", ["reject", "hire"])
def test_final_states_cannot_change(terminal):
    aid = new_application()
    act(aid, "employer@example.com", "mark_reviewed")
    act(aid, "employer@example.com", "shortlist")
    assert act(aid, "employer@example.com", terminal).status_code == 200
    for action in ("mark_reviewed", "shortlist", "reject", "hire"):
        assert act(aid, "employer@example.com", action).status_code == 409


def test_reopen_is_gone():
    aid = new_application()
    act(aid, "employer@example.com", "mark_reviewed")
    act(aid, "employer@example.com", "reject")
    assert act(aid, "employer@example.com", "reopen").status_code == 409


def test_admin_cannot_change_status():
    aid = new_application()
    assert act(aid, "admin@example.com", "mark_reviewed").status_code == 403


def test_other_employer_cannot_change_status():
    aid = new_application()
    assert act(aid, "employer2@example.com", "mark_reviewed").status_code == 403


def test_graduate_cannot_change_status():
    aid = new_application()
    assert act(aid, "grad.dcit@example.com", "mark_reviewed").status_code == 403


def test_unknown_application_is_404():
    assert act(9999, "employer@example.com", "mark_reviewed").status_code == 404


def test_other_employer_cannot_view_applicants():
    new_application()
    r = client.get("/api/listings/1/applicants", params={"actor_id": uid("employer2@example.com")})
    assert r.status_code == 403
    r = client.get("/api/listings/1/applicants", params={"actor_id": uid("employer@example.com")})
    assert r.status_code == 200


def test_flags_match_status():
    aid = new_application()
    body = act(aid, "employer@example.com", "mark_reviewed").json()["application"]

    assert body["status"] == "reviewed"
    assert body["flag_reviewed"] == 1
    assert body["flag_shortlisted"] == 0
    assert body["flag_rejected"] == 0
    assert body["flag_hired"] == 0
