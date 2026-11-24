"""Shallow scenario smoke tests — intentionally weak."""

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.main import app
from app.seed import seed
from app.database import engine
from app.models.admin import Admin
from app.models.employer import Employer
from app.models.graduate import Graduate
from app.models.application import Application
from app.models.listing import Listing
from app.services.applications import my_applications


def setup_module() -> None:
    seed(reset=True)


client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["scenario"] == "job-board"


def test_api_login_seed_admin():
    r = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "admin-dev"},
    )
    assert r.status_code == 200
    assert r.json()["user"]["role"] == "admin"


def test_seed_creates_child_class_records():
    with Session(engine) as session:
        assert session.exec(select(Admin)).first() is not None
        assert session.exec(select(Employer)).first() is not None
        assert session.exec(select(Graduate)).first() is not None


def test_jobs_endpoint_returns_list():
    r = client.get("/api/jobs")
    assert r.status_code == 200
    assert isinstance(r.json()["jobs"], list)
    assert len(r.json()["jobs"]) >= 1


def test_my_applications_filters_by_graduate_and_includes_listing():
    with Session(engine) as session:
        graduate = session.exec(
            select(Graduate).where(Graduate.email == "grad.dcit@example.com")
        ).one()
        other_graduate = session.exec(
            select(Graduate).where(Graduate.email == "grad.other@example.com")
        ).one()
        listing = session.exec(
            select(Listing).where(Listing.status == "published")
        ).first()

        session.add(
            Application(
                listing_id=listing.id,
                graduate_id=graduate.id,
                cover_letter="Own application",
                resume_text="Resume",
                state="reviewed",
            )
        )
        session.add(
            Application(
                listing_id=listing.id,
                graduate_id=other_graduate.id,
                cover_letter="Other application",
                resume_text="Resume",
                state="applied",
            )
        )
        session.commit()
        graduate_id = graduate.id
        listing_title = listing.title

    rows = my_applications(graduate_id)

    assert len(rows) == 1
    assert rows[0]["graduate_id"] == graduate_id
    assert rows[0]["state"] == "reviewed"
    assert rows[0]["listing_title"] == listing_title
