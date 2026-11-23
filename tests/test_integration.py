import jwt
import pytest
from sqlmodel import Session

from app.config import get_settings
from app.models.application import Application
from app.models.listing import Listing
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.utilities.security import verify_password
from app.services.applications import transition_application


def test_save_password(test_session):
    repository = UserRepository(test_session)
    service = AuthService(repository)

    created = service.register_user("alice", "alice@example.com", "secret")
    saved = repository.get_by_username("alice")

    assert saved is not None
    assert created.id == saved.id
    assert saved.username == "alice"
    assert saved.email == "alice@example.com"
    assert saved.role == "regular_user"
    assert saved.password != "secret"
    assert verify_password("secret", saved.password)


def test_login(test_session):
    repository = UserRepository(test_session)
    service = AuthService(repository)
    service.register_user("alice", "alice@example.com", "secret")

    token = service.authenticate_user("alice", "secret")
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == str(repository.get_by_username("alice").id)
    assert payload["role"] == "regular_user"


def test_register_user(test_session):
    repository = UserRepository(test_session)
    auth_service = AuthService(repository)
    auth_service.register_user("alice", "alice@example.com", "secret")

    users = UserService(repository).get_all_users()

    assert len(users) == 1
    assert users[0].username == "alice"
    assert users[0].email == "alice@example.com"


@pytest.fixture
def lifecycle_records(lifecycle_db):
    with Session(lifecycle_db) as session:
        owner = User(
            username="owner",
            email="owner@example.com",
            password="unused",
            role="employer",
        )
        other = User(
            username="other",
            email="other@example.com",
            password="unused",
            role="employer",
        )
        admin = User(
            username="admin",
            email="admin@example.com",
            password="unused",
            role="admin",
        )
        graduate = User(
            username="graduate",
            email="graduate@example.com",
            password="unused",
            role="graduate",
            programme="DCIT",
        )
        session.add_all([owner, other, admin, graduate])
        session.commit()
        session.refresh(owner)
        session.refresh(other)
        session.refresh(admin)
        session.refresh(graduate)

        listing = Listing(
            employer_id=owner.id,
            title="Lifecycle Role",
            company="Test Co",
            description="Lifecycle integration test",
            apply_mode="collect",
            external_url=None,
            deadline="2099-12-31",
            status="published",
        )
        session.add(listing)
        session.commit()
        session.refresh(listing)

        application = Application(
            listing_id=listing.id,
            graduate_id=graduate.id,
            cover_letter="Test letter",
            resume_text="Test resume",
            status="submitted",
        )
        session.add(application)
        session.commit()
        session.refresh(application)

        return {
            "owner_id": owner.id,
            "other_id": other.id,
            "admin_id": admin.id,
            "graduate_id": graduate.id,
            "listing_id": listing.id,
            "application_id": application.id,
        }


def test_owner_can_drive_full_lifecycle(lifecycle_db, lifecycle_records):
    application_id = lifecycle_records["application_id"]
    owner_id = lifecycle_records["owner_id"]

    moves = [
        ("review", "reviewed"),
        ("shortlist", "shortlisted"),
        ("hire", "hired"),
    ]
    for action, expected_status in moves:
        result = transition_application(owner_id, application_id, action)
        assert result["ok"] is True
        assert result["changed"] is True
        assert result["application"]["status"] == expected_status

    with Session(lifecycle_db) as session:
        application = session.get(Application, application_id)
        assert application.status == "hired"


def test_rejected_application_can_be_reopened(lifecycle_db, lifecycle_records):
    application_id = lifecycle_records["application_id"]
    owner_id = lifecycle_records["owner_id"]

    assert transition_application(owner_id, application_id, "review")["ok"] is True
    assert (
        transition_application(owner_id, application_id, "reject")["ok"] is True
    )

    reopened = transition_application(owner_id, application_id, "reopen")
    assert reopened["ok"] is True
    assert reopened["application"]["status"] == "reviewed"

    with Session(lifecycle_db) as session:
        application = session.get(Application, application_id)
        assert application.status == "reviewed"


def test_illegal_transition_is_refused(lifecycle_db, lifecycle_records):
    result = transition_application(
        lifecycle_records["owner_id"],
        lifecycle_records["application_id"],
        "hire",
    )

    assert result["ok"] is False
    assert result["code"] == "illegal_transition"


@pytest.mark.parametrize("actor_key", ["other_id", "admin_id"])
def test_non_owner_and_admin_cannot_transition(
    lifecycle_db, lifecycle_records, actor_key
):
    result = transition_application(
        lifecycle_records[actor_key],
        lifecycle_records["application_id"],
        "review",
    )

    assert result["ok"] is False
    assert result["code"] == "forbidden"
