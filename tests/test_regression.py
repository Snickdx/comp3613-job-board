"""Regression tests for the Sprint 1 defect audits (S2-#9).

Each test is named after the defect it guards against:
- D1–D7: docs/Deliverables/Defects/LifecycleAudit.md
- A2–A7: docs/Deliverables/Defects/AuthListingsAudit.md

The tests go through the JSON API, so they check both the behaviour and the
HTTP status codes from S2-#8. They use their own in-memory database seeded
like app/seed.py, so user and listing ids match the audit write-ups.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.main import app
from app.models.application import Application
from app.models.listing import Listing
from app.models.user import User

# Ids match the seed data used in both audits.
ADMIN, GRAD_DCIT, GRAD_OTHER, EMPLOYER, EMPLOYER2 = 1, 2, 3, 4, 5
OPEN_LISTING, PENDING_EXTERNAL_LISTING, EXPIRED_LISTING = 1, 2, 3


@pytest.fixture
def audit_db(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    # Every service that opens its own session must use the test database.
    for module in ("applications", "listings", "board_auth"):
        monkeypatch.setattr(f"app.services.{module}.engine", engine)

    with Session(engine) as session:
        session.add_all(
            [
                User(username="admin", email="admin@example.com", password="x", role="admin"),
                User(username="grad.dcit", email="grad.dcit@example.com", password="x", role="graduate", programme="DCIT"),
                User(username="grad.other", email="grad.other@example.com", password="x", role="graduate", programme="OTHER"),
                User(username="employer", email="employer@example.com", password="x", role="employer"),
                User(username="employer2", email="employer2@example.com", password="x", role="employer"),
            ]
        )
        session.commit()
        session.add_all(
            [
                Listing(employer_id=EMPLOYER, title="Junior Software Engineer", company="Acme Soft", description="d", apply_mode="collect", deadline="2099-12-31", status="published"),
                Listing(employer_id=EMPLOYER, title="QA Intern", company="Acme Soft", description="d", apply_mode="external", external_url="https://example.com/apply/qa", deadline="2099-06-30", status="pending"),
                Listing(employer_id=EMPLOYER2, title="Expired Analyst Role", company="PastCo", description="d", apply_mode="collect", deadline="2020-01-01", status="published"),
            ]
        )
        session.commit()

    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def client(audit_db):
    return TestClient(app)


@pytest.fixture
def application_id(client):
    """An application from the DCIT graduate to the open listing, status 'submitted'."""
    response = client.post(
        "/api/graduates/applications",
        json={"actor_id": GRAD_DCIT, "listing_id": OPEN_LISTING, "cover_letter": "Hello"},
    )
    assert response.status_code == 200
    return response.json()["application_id"]


def transition(client, application_id, action, actor=EMPLOYER):
    return client.post(
        f"/api/applications/{application_id}/transition",
        json={"action": action, "actor_id": actor},
    )


def stored_status(engine, application_id):
    with Session(engine) as session:
        return session.get(Application, application_id).status


def application_count(engine):
    with Session(engine) as session:
        return len(session.exec(select(Application)).all())


# ---------------------------------------------------------------------------
# Lifecycle defects (special feature, State pattern)
# ---------------------------------------------------------------------------


def test_D1_hire_from_submitted_is_refused(client, audit_db, application_id):
    response = transition(client, application_id, "hire")

    assert response.status_code == 409
    assert stored_status(audit_db, application_id) == "submitted"


def test_D2_rejected_application_cannot_be_shortlisted(client, audit_db, application_id):
    assert transition(client, application_id, "review").status_code == 200
    assert transition(client, application_id, "reject").status_code == 200

    response = transition(client, application_id, "shortlist")

    assert response.status_code == 409
    assert stored_status(audit_db, application_id) == "rejected"


def test_D3_reopen_leaves_one_consistent_status(client, audit_db, application_id):
    transition(client, application_id, "review")
    transition(client, application_id, "reject")

    response = transition(client, application_id, "reopen")

    assert response.status_code == 200
    assert response.json()["application"]["status"] == "reviewed"
    # The four parallel flags that caused D3 no longer exist.
    for flag in ("flag_reviewed", "flag_shortlisted", "flag_rejected", "flag_hired"):
        assert flag not in Application.model_fields


def test_D4_graduate_and_employer_see_the_same_status(client, application_id):
    for action in ("review", "shortlist", "hire"):
        transition(client, application_id, action)

        graduate_view = client.get(
            "/api/graduates/applications", params={"actor_id": GRAD_DCIT}
        ).json()["applications"]
        employer_view = client.get(
            f"/api/listings/{OPEN_LISTING}/applicants", params={"actor_id": EMPLOYER}
        ).json()["applicants"]

        assert graduate_view[0]["status"] == employer_view[0]["status"]


@pytest.mark.parametrize("actor", [EMPLOYER2, ADMIN], ids=["other_employer", "admin"])
def test_D5_only_listing_employer_can_transition(client, audit_db, application_id, actor):
    response = transition(client, application_id, "review", actor=actor)

    assert response.status_code == 403
    assert stored_status(audit_db, application_id) == "submitted"


def test_D6_illegal_action_on_hired_is_an_error_not_silent_ok(client, application_id):
    for action in ("review", "shortlist", "hire"):
        transition(client, application_id, action)

    response = transition(client, application_id, "review")

    assert response.status_code == 409
    assert "hired" in response.json()["detail"]


def test_D7_transition_response_matches_stored_application(client, application_id):
    response = transition(client, application_id, "review")

    returned = response.json()["application"]
    stored = client.get(
        f"/api/listings/{OPEN_LISTING}/applicants", params={"actor_id": EMPLOYER}
    ).json()["applicants"][0]
    assert returned == stored


def test_unknown_action_returns_400(client, application_id):
    assert transition(client, application_id, "promote").status_code == 400


def test_missing_application_returns_404(client):
    assert transition(client, 999, "review").status_code == 404


# ---------------------------------------------------------------------------
# Authorization & listings defects
# ---------------------------------------------------------------------------


def test_A2_ineligible_graduate_cannot_subscribe(client):
    assert client.post("/api/graduates/subscribe", json={"actor_id": GRAD_OTHER}).status_code == 400
    assert client.post("/api/graduates/subscribe", json={"actor_id": GRAD_DCIT}).status_code == 200


def test_A3_ineligible_graduate_cannot_apply(client, audit_db):
    response = client.post(
        "/api/graduates/applications",
        json={"actor_id": GRAD_OTHER, "listing_id": OPEN_LISTING, "cover_letter": "Hi"},
    )

    assert response.status_code == 400
    assert application_count(audit_db) == 0


def test_A4_job_list_hides_pending_and_expired_listings(client):
    jobs = client.get("/api/jobs").json()["jobs"]

    assert [job["id"] for job in jobs] == [OPEN_LISTING]


def test_A5_cannot_apply_to_expired_listing(client, audit_db):
    response = client.post(
        "/api/graduates/applications",
        json={"actor_id": GRAD_DCIT, "listing_id": EXPIRED_LISTING, "cover_letter": "Hi"},
    )

    assert response.status_code == 400
    assert application_count(audit_db) == 0


def test_A6_cannot_apply_in_app_to_pending_or_external_listing(client, audit_db):
    apply = lambda: client.post(
        "/api/graduates/applications",
        json={"actor_id": GRAD_DCIT, "listing_id": PENDING_EXTERNAL_LISTING, "cover_letter": "Hi"},
    )

    # Still pending: hidden from graduates.
    assert apply().status_code == 400

    # Once published it is visible, but it is external-link, so no row is stored (AC 13).
    client.post(f"/api/admin/listings/{PENDING_EXTERNAL_LISTING}/publish", json={"actor_id": ADMIN})
    response = apply()

    assert response.status_code == 400
    assert "externally" in response.json()["detail"]
    assert application_count(audit_db) == 0


def test_A7_employer_cannot_view_another_employers_applicants(client, application_id):
    other = client.get(f"/api/listings/{OPEN_LISTING}/applicants", params={"actor_id": EMPLOYER2})
    owner = client.get(f"/api/listings/{OPEN_LISTING}/applicants", params={"actor_id": EMPLOYER})
    admin = client.get(f"/api/admin/listings/{OPEN_LISTING}/export", params={"actor_id": ADMIN})

    assert other.status_code == 403
    assert owner.status_code == 200
    assert admin.status_code == 200  # AC 16: admin export still allowed
