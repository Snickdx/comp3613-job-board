"""Regression tests for the Sprint 1 defect audits (S2-#9).

Each test is named after the defect it guards against:
- D1–D7: docs/Deliverables/Defects/LifecycleAudit.md
- A1–A10: docs/Deliverables/Defects/AuthListingsAudit.md

The tests go through the JSON API, so they check both the behaviour and the
HTTP status codes from S2-#8. They use their own in-memory database seeded
like app/seed.py, so user and listing ids match the audit write-ups.

Since S2-#11 the API identifies the caller from the JWT session cookie
(AuthDep / AdminDep). The `login_as` fixture stands in for a logged-in user by
overriding get_current_user, so each test can act as a specific seeded user.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.dependencies.auth import get_current_user
from app.main import app
from app.models.application import Application
from app.models.listing import Listing
from app.models.notification import Notification
from app.models.subscription import Subscription
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
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def login_as(audit_db):
    """Act as a seeded user: the API's get_current_user returns that user."""

    def _login_as(user_id):
        with Session(audit_db) as session:
            user = session.get(User, user_id)
        app.dependency_overrides[get_current_user] = lambda: user

    return _login_as


@pytest.fixture
def application_id(client, login_as):
    """An application from the DCIT graduate to the open listing, status 'submitted'."""
    login_as(GRAD_DCIT)
    response = apply_to(client, OPEN_LISTING)
    assert response.status_code == 200
    return response.json()["application_id"]


# Request bodies still declare actor_id (S2-#11 left it in the schema). The API
# ignores it now; the caller always comes from the session. Sending 0 makes that
# obvious, and test_A1_actor_id_in_body_is_ignored checks it.
IGNORED_ACTOR_ID = 0


def apply_to(client, listing_id):
    return client.post(
        "/api/graduates/applications",
        json={"listing_id": listing_id, "cover_letter": "Hello", "actor_id": IGNORED_ACTOR_ID},
    )


def transition(client, login_as, application_id, action, actor=EMPLOYER):
    login_as(actor)
    return client.post(
        f"/api/applications/{application_id}/transition",
        json={"action": action, "actor_id": IGNORED_ACTOR_ID},
    )


def stored_status(engine, application_id):
    with Session(engine) as session:
        return session.get(Application, application_id).status


def application_count(engine):
    with Session(engine) as session:
        return len(session.exec(select(Application)).all())


def notifications_for(engine, user_id, listing_id):
    with Session(engine) as session:
        return session.exec(
            select(Notification).where(
                Notification.user_id == user_id, Notification.listing_id == listing_id
            )
        ).all()


def submit_listing(client, login_as):
    login_as(EMPLOYER)
    response = client.post(
        "/api/employer/listings",
        json={
            "title": "Backend Intern",
            "company": "Acme Soft",
            "description": "APIs",
            "apply_mode": "collect",
            "deadline": "2099-12-31",
        },
    )
    assert response.status_code == 200
    return response.json()


# ---------------------------------------------------------------------------
# Lifecycle defects (special feature, State pattern)
# ---------------------------------------------------------------------------


def test_D1_hire_from_submitted_is_refused(client, login_as, audit_db, application_id):
    response = transition(client, login_as, application_id, "hire")

    assert response.status_code == 409
    assert stored_status(audit_db, application_id) == "submitted"


def test_D2_rejected_application_cannot_be_shortlisted(client, login_as, audit_db, application_id):
    assert transition(client, login_as, application_id, "review").status_code == 200
    assert transition(client, login_as, application_id, "reject").status_code == 200

    response = transition(client, login_as, application_id, "shortlist")

    assert response.status_code == 409
    assert stored_status(audit_db, application_id) == "rejected"


def test_D3_reopen_leaves_one_consistent_status(client, login_as, application_id):
    transition(client, login_as, application_id, "review")
    transition(client, login_as, application_id, "reject")

    response = transition(client, login_as, application_id, "reopen")

    assert response.status_code == 200
    assert response.json()["application"]["status"] == "reviewed"
    # The four parallel flags that caused D3 no longer exist.
    for flag in ("flag_reviewed", "flag_shortlisted", "flag_rejected", "flag_hired"):
        assert flag not in Application.model_fields


def test_D4_graduate_and_employer_see_the_same_status(client, login_as, application_id):
    for action in ("review", "shortlist", "hire"):
        transition(client, login_as, application_id, action)

        login_as(GRAD_DCIT)
        graduate_view = client.get("/api/graduates/applications").json()["applications"]
        login_as(EMPLOYER)
        employer_view = client.get(f"/api/listings/{OPEN_LISTING}/applicants").json()["applicants"]

        assert graduate_view[0]["status"] == employer_view[0]["status"]


@pytest.mark.parametrize("actor", [EMPLOYER2, ADMIN], ids=["other_employer", "admin"])
def test_D5_only_listing_employer_can_transition(client, login_as, audit_db, application_id, actor):
    response = transition(client, login_as, application_id, "review", actor=actor)

    assert response.status_code == 403
    assert stored_status(audit_db, application_id) == "submitted"


def test_D6_illegal_action_on_hired_is_an_error_not_silent_ok(client, login_as, application_id):
    for action in ("review", "shortlist", "hire"):
        transition(client, login_as, application_id, action)

    response = transition(client, login_as, application_id, "review")

    assert response.status_code == 409
    assert "hired" in response.json()["detail"]


def test_D7_transition_response_matches_stored_application(client, login_as, application_id):
    response = transition(client, login_as, application_id, "review")

    returned = response.json()["application"]
    stored = client.get(f"/api/listings/{OPEN_LISTING}/applicants").json()["applicants"][0]
    assert returned == stored


def test_unknown_action_returns_400(client, login_as, application_id):
    assert transition(client, login_as, application_id, "promote").status_code == 400


def test_missing_application_returns_404(client, login_as):
    assert transition(client, login_as, 999, "review").status_code == 404


# ---------------------------------------------------------------------------
# Authorization & listings defects
# ---------------------------------------------------------------------------


def test_A1_requests_without_a_session_are_rejected(client, application_id):
    app.dependency_overrides.clear()  # no logged-in user

    response = client.post(
        f"/api/applications/{application_id}/transition",
        json={"action": "review", "actor_id": EMPLOYER},
    )

    assert response.status_code == 401


def test_A1_actor_id_in_body_is_ignored(client, login_as, audit_db, application_id):
    # Logged in as employer2 but claiming to be the listing owner in the body.
    login_as(EMPLOYER2)
    response = client.post(
        f"/api/applications/{application_id}/transition",
        json={"action": "review", "actor_id": EMPLOYER},
    )

    assert response.status_code == 403
    assert stored_status(audit_db, application_id) == "submitted"


def test_A2_ineligible_graduate_cannot_subscribe(client, login_as):
    login_as(GRAD_OTHER)
    assert client.post("/api/graduates/subscribe").status_code == 400
    login_as(GRAD_DCIT)
    assert client.post("/api/graduates/subscribe").status_code == 200


def test_A3_ineligible_graduate_cannot_apply(client, login_as, audit_db):
    login_as(GRAD_OTHER)
    response = apply_to(client, OPEN_LISTING)

    assert response.status_code == 400
    assert application_count(audit_db) == 0


def test_A4_job_list_hides_pending_and_expired_listings(client):
    jobs = client.get("/api/jobs").json()["jobs"]

    assert [job["id"] for job in jobs] == [OPEN_LISTING]


def test_authenticated_jobs_page_renders_current_listings(client, login_as):
    login_as(EMPLOYER)
    response = client.get("/jobs")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Junior Software Engineer" in response.text
    assert "Acme Soft" in response.text
    assert "QA Intern" not in response.text
    assert "Expired Analyst Role" not in response.text


def test_A5_cannot_apply_to_expired_listing(client, login_as, audit_db):
    login_as(GRAD_DCIT)
    response = apply_to(client, EXPIRED_LISTING)

    assert response.status_code == 400
    assert application_count(audit_db) == 0


def test_A6_cannot_apply_in_app_to_pending_or_external_listing(client, login_as, audit_db):
    # Still pending: hidden from graduates.
    login_as(GRAD_DCIT)
    assert apply_to(client, PENDING_EXTERNAL_LISTING).status_code == 400

    # Once published it is visible, but it is external-link, so no row is stored (AC 13).
    login_as(ADMIN)
    assert client.post(f"/api/admin/listings/{PENDING_EXTERNAL_LISTING}/publish").status_code == 200
    login_as(GRAD_DCIT)
    response = apply_to(client, PENDING_EXTERNAL_LISTING)

    assert response.status_code == 400
    assert "externally" in response.json()["detail"]
    assert application_count(audit_db) == 0


def test_A7_employer_cannot_view_another_employers_applicants(client, login_as, application_id):
    login_as(EMPLOYER2)
    other = client.get(f"/api/listings/{OPEN_LISTING}/applicants")
    login_as(EMPLOYER)
    owner = client.get(f"/api/listings/{OPEN_LISTING}/applicants")
    login_as(ADMIN)
    admin = client.get(f"/api/admin/listings/{OPEN_LISTING}/export")

    assert other.status_code == 403
    assert owner.status_code == 200
    assert admin.status_code == 200  # AC 16: admin export still allowed


def test_A8_new_listing_is_pending_until_an_admin_publishes_it(client, login_as):
    created = submit_listing(client, login_as)
    listing_id = created["listing_id"]

    assert created["status"] == "pending"
    assert listing_id not in [job["id"] for job in client.get("/api/jobs").json()["jobs"]]
    login_as(ADMIN)
    pending = client.get("/api/admin/listings/pending").json()["listings"]
    assert listing_id in [listing["id"] for listing in pending]

    assert client.post(f"/api/admin/listings/{listing_id}/publish").status_code == 200

    assert listing_id in [job["id"] for job in client.get("/api/jobs").json()["jobs"]]


def test_A9_publishing_notifies_subscribers_automatically(client, login_as, audit_db):
    login_as(GRAD_DCIT)
    assert client.post("/api/graduates/subscribe").status_code == 200
    listing_id = submit_listing(client, login_as)["listing_id"]

    login_as(ADMIN)
    response = client.post(f"/api/admin/listings/{listing_id}/publish")

    assert response.json()["notified"] == 1
    assert len(notifications_for(audit_db, GRAD_DCIT, listing_id)) == 1


def test_A10_notify_skips_ineligible_subscribers_and_duplicates(client, login_as, audit_db):
    # An ineligible subscription left over from before A2 was fixed.
    with Session(audit_db) as session:
        session.add_all([Subscription(graduate_id=GRAD_DCIT), Subscription(graduate_id=GRAD_OTHER)])
        session.commit()
    listing_id = submit_listing(client, login_as)["listing_id"]

    login_as(ADMIN)
    published = client.post(f"/api/admin/listings/{listing_id}/publish")
    resent = client.post(f"/api/admin/listings/{listing_id}/notify")

    assert published.json()["notified"] == 1
    assert resent.json()["count"] == 0
    assert len(notifications_for(audit_db, GRAD_DCIT, listing_id)) == 1
    assert notifications_for(audit_db, GRAD_OTHER, listing_id) == []
