import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.main import app
from app.database import engine
from app.models.admin import Admin
from app.models.application import Application
from app.models.employer import Employer
from app.models.graduate import Graduate
from app.models.listing import Listing
from app.seed import seed
from app.utilities.security import create_access_token


client = TestClient(app)


@pytest.fixture(autouse=True)
def application_test_data(isolated_test_database):
    assert engine.url.database.endswith("application-tests.db")
    seed(reset=True)
    yield


def auth_cookie(user_id: int) -> dict[str, str]:
    token = create_access_token({"sub": str(user_id)})
    return {"Cookie": f"access_token={token}"}


def seed_ids() -> tuple[int, int, int, int]:
    with Session(engine) as session:
        dcit = session.exec(
            select(Graduate).where(Graduate.programme == "DCIT")
        ).one()
        other = session.exec(
            select(Graduate).where(Graduate.programme == "OTHER")
        ).one()
        employer = session.exec(
            select(Employer).where(Employer.email == "employer@example.com")
        ).one()
        listing = session.exec(
            select(Listing).where(Listing.apply_mode == "collect")
        ).first()
        assert listing is not None
        return dcit.id, other.id, employer.id, listing.id


def create_application(graduate_id: int, listing_id: int) -> int:
    from app.services.applications import apply

    result = apply(graduate_id, listing_id, "Cover letter", "Resume")
    assert result["ok"] is True
    return result["application_id"]


def test_application_requests_require_authentication():
    response = client.get("/api/graduates/applications")
    assert response.status_code == 401


def test_application_tests_use_the_temporary_sqlite_database(isolated_test_database):
    assert isolated_test_database.url.get_backend_name() == "sqlite"
    assert engine.url.database.endswith("application-tests.db")


@pytest.mark.parametrize("action", ["transition", "__class__", "model_dump"])
def test_state_transition_rejects_non_lifecycle_actions(action):
    application = Application(
        listing_id=1,
        graduate_id=1,
        cover_letter="Cover letter",
        resume_text="Resume",
    )

    assert application.transition(action) is False
    assert application.state == "submitted"


@pytest.mark.parametrize(
    ("state", "action"),
    [
        ("submitted", "interview"),
        ("shortlisted", "interview"),
        ("reviewed", "offer"),
        ("shortlisted", "withdraw"),
        ("interview", "offer"),
    ],
)
def test_legacy_lifecycle_paths_are_inactive(state, action):
    application = Application(
        listing_id=1,
        graduate_id=1,
        cover_letter="Cover letter",
        resume_text="Resume",
        state=state,
    )

    assert application.transition(action) is False
    assert application.state == state


def test_graduate_starts_application_at_submitted():
    dcit_id, _, _, listing_id = seed_ids()

    from app.services.applications import apply

    result = apply(dcit_id, listing_id, "I am interested.", "Python resume")
    assert result["ok"] is True
    assert result["state"] == "submitted"


def test_graduate_other_programme_cannot_apply():
    _, other_id, _, listing_id = seed_ids()

    from app.services.applications import apply

    result = apply(other_id, listing_id, "Cover letter", "Resume")
    assert result == {"ok": False, "error": "graduate is not eligible"}


def test_external_listing_cannot_create_application():
    dcit_id, _, _, _ = seed_ids()

    from app.services.applications import apply

    with Session(engine) as session:
        external = session.exec(
            select(Listing).where(Listing.apply_mode == "external")
        ).one()

    result = apply(dcit_id, external.id, "Cover letter", "Resume")
    assert result["ok"] is False
    assert "external" in result["error"]


def test_application_endpoint_returns_validation_and_conflict_statuses():
    dcit_id, _, employer_id, listing_id = seed_ids()

    invalid_application = client.post(
        "/api/graduates/applications",
        headers=auth_cookie(dcit_id),
        json={
            "listing_id": listing_id,
            "cover_letter": " ",
            "resume_text": "Resume",
        },
    )
    assert invalid_application.status_code == 422

    missing_listing = client.post(
        "/api/graduates/applications",
        headers=auth_cookie(dcit_id),
        json={
            "listing_id": 99999,
            "cover_letter": "Cover letter",
            "resume_text": "Resume",
        },
    )
    assert missing_listing.status_code == 404

    application_id = create_application(dcit_id, listing_id)
    invalid_action = client.post(
        f"/api/applications/{application_id}/transition",
        headers=auth_cookie(employer_id),
        json={"action": "interview"},
    )
    invalid_transition = client.post(
        f"/api/applications/{application_id}/transition",
        headers=auth_cookie(employer_id),
        json={"action": "hire"},
    )
    missing_application = client.post(
        "/api/applications/99999/transition",
        headers=auth_cookie(employer_id),
        json={"action": "review"},
    )
    assert invalid_action.status_code == 422
    assert invalid_transition.status_code == 409
    assert missing_application.status_code == 404


def test_employer_ownership_and_invalid_transition():
    dcit_id, _, employer_id, listing_id = seed_ids()

    from app.services.applications import apply, transition_application

    created = apply(dcit_id, listing_id, "Cover letter", "Resume")
    application_id = created["application_id"]

    forbidden = transition_application(
        actor_id=employer_id + 100,
        application_id=application_id,
        action="review",
    )
    assert forbidden["ok"] is False
    assert forbidden["error"] == "forbidden"

    invalid = transition_application(
        actor_id=employer_id,
        application_id=application_id,
        action="hire",
    )
    assert invalid["ok"] is False
    assert invalid["error"] == "invalid application state transition"

    with Session(engine) as session:
        application = session.get(Application, application_id)
        assert application.state == "submitted"


def test_employer_can_complete_valid_transition_and_persist():
    dcit_id, _, employer_id, listing_id = seed_ids()

    from app.services.applications import apply, transition_application

    created = apply(dcit_id, listing_id, "Cover letter", "Resume")
    application_id = created["application_id"]

    reviewed = transition_application(employer_id, application_id, "review")
    assert reviewed["ok"] is True
    shortlisted = transition_application(employer_id, application_id, "shortlist")
    assert shortlisted["ok"] is True
    hired = transition_application(employer_id, application_id, "hire")
    assert hired["ok"] is True

    with Session(engine) as session:
        application = session.get(Application, application_id)
        assert application.state == "hired"


def test_graduate_cannot_execute_employer_transition_via_http():
    dcit_id, _, _, listing_id = seed_ids()

    from app.services.applications import apply

    created = apply(dcit_id, listing_id, "Cover letter", "Resume")
    response = client.post(
        f"/api/applications/{created['application_id']}/transition",
        headers=auth_cookie(dcit_id),
        json={"action": "review"},
    )
    assert response.status_code == 403


def test_admin_cannot_execute_application_transition():
    dcit_id, _, _, listing_id = seed_ids()
    with Session(engine) as session:
        admin = session.exec(select(Admin)).one()
    application_id = create_application(dcit_id, listing_id)

    response = client.post(
        f"/api/applications/{application_id}/transition",
        headers=auth_cookie(admin.id),
        json={"action": "review"},
    )
    assert response.status_code == 403


def test_employer_cannot_transition_another_employers_application():
    dcit_id, _, employer_id, listing_id = seed_ids()
    application_id = create_application(dcit_id, listing_id)

    with Session(engine) as session:
        other_employer = session.exec(
            select(Employer).where(Employer.email == "employer2@example.com")
        ).one()

    response = client.post(
        f"/api/applications/{application_id}/transition",
        headers=auth_cookie(other_employer.id),
        json={"action": "review"},
    )
    assert response.status_code == 403
    assert employer_id != other_employer.id


def test_graduate_cannot_access_another_graduates_applications():
    dcit_id, other_id, _, listing_id = seed_ids()
    dcit_application_id = create_application(dcit_id, listing_id)
    with Session(engine) as session:
        other_application = Application(
            listing_id=listing_id,
            graduate_id=other_id,
            cover_letter="Cover letter",
            resume_text="Resume",
            state="submitted",
        )
        session.add(other_application)
        session.commit()
        session.refresh(other_application)
        other_application_id = other_application.id

    response = client.get(
        "/api/graduates/applications",
        headers=auth_cookie(dcit_id),
    )
    assert response.status_code == 200
    returned_ids = {
        application["id"] for application in response.json()["applications"]
    }
    assert dcit_application_id in returned_ids
    assert other_application_id not in returned_ids


@pytest.mark.parametrize(
    ("terminal_action", "terminal_state"),
    [("hire", "hired"), ("reject", "rejected")],
)
def test_terminal_application_cannot_be_reopened(terminal_action, terminal_state):
    dcit_id, _, employer_id, listing_id = seed_ids()
    application_id = create_application(dcit_id, listing_id)

    from app.services.applications import transition_application

    for action in ("review", "shortlist", terminal_action):
        result = transition_application(employer_id, application_id, action)
        assert result["ok"] is True

    reopened = transition_application(employer_id, application_id, "review")
    assert reopened == {
        "ok": False,
        "error": "invalid application state transition",
    }
    with Session(engine) as session:
        assert session.get(Application, application_id).state == terminal_state


def test_overlapping_role_records_are_rejected_over_http():
    dcit_id, _, _, listing_id = seed_ids()
    with Session(engine) as session:
        session.add(
            Employer(
                id=dcit_id,
                username="overlapping-employer",
                email="overlapping-employer@example.com",
                password="not-used",
            )
        )
        session.commit()
    application_id = create_application(dcit_id, listing_id)

    own_applications = client.get(
        "/api/graduates/applications",
        headers=auth_cookie(dcit_id),
    )
    transition_response = client.post(
        f"/api/applications/{application_id}/transition",
        headers=auth_cookie(dcit_id),
        json={"action": "review"},
    )
    assert own_applications.status_code == 403
    assert transition_response.status_code == 403


def test_admin_export_is_allowed_and_non_admin_export_is_forbidden():
    dcit_id, _, employer_id, listing_id = seed_ids()
    application_id = create_application(dcit_id, listing_id)
    with Session(engine) as session:
        admin = session.exec(select(Admin)).one()

    allowed = client.get(
        f"/api/admin/listings/{listing_id}/export",
        headers=auth_cookie(admin.id),
    )
    denied = client.get(
        f"/api/admin/listings/{listing_id}/export",
        headers=auth_cookie(employer_id),
    )
    assert allowed.status_code == 200
    assert allowed.json()["package"][0]["id"] == application_id
    assert denied.status_code == 403


def test_employer_cannot_list_another_employers_applicants():
    _, _, _, listing_id = seed_ids()
    with Session(engine) as session:
        other_employer = session.exec(
            select(Employer).where(Employer.email == "employer2@example.com")
        ).one()
        other_listing = session.exec(
            select(Listing).where(Listing.employer_id == other_employer.id)
        ).first()

    assert other_listing is not None
    response = client.get(
        f"/api/listings/{listing_id}/applicants",
        headers=auth_cookie(other_employer.id),
    )
    assert response.status_code == 403
