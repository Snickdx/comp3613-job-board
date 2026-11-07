"""Seed demo users and sample listings for the job-board scenario."""

from __future__ import annotations

from sqlmodel import Session, select

from app.database import drop_all, ensure_db_and_tables, engine
from app.models.listing import Listing
from app.models.subscription import Subscription
from app.models.user import User
from app.utilities.security import encrypt_password

USERS = [
    # username, email, password, role, programme, field, resume
    ("admin", "admin@example.com", "admin-dev", "admin", None, None, None),
    (
        "grad.dcit",
        "grad.dcit@example.com",
        "grad-dev",
        "graduate",
        "DCIT",
        "software",
        "DCIT graduate resume - Python, web.",
    ),
    (
        "grad.other",
        "grad.other@example.com",
        "grad-dev",
        "graduate",
        "OTHER",
        "biology",
        "Non-DCIT resume.",
    ),
    ("employer", "employer@example.com", "employer-dev", "employer", None, None, None),
    ("employer2", "employer2@example.com", "employer-dev", "employer", None, None, None),
]


def seed(*, reset: bool = False) -> None:
    import app.models  # noqa: F401

    if reset:
        try:
            drop_all()
        except Exception:
            pass
    ensure_db_and_tables()

    with Session(engine) as session:
        existing = session.exec(select(User)).first()
        if existing and not reset:
            return
        if existing and reset:
            # Tables were dropped above; continue to insert.
            pass

        for username, email, password, role, programme, field, resume in USERS:
            session.add(
                User(
                    username=username,
                    email=email,
                    password=encrypt_password(password),
                    role=role,
                    programme=programme,
                    field_preference=field,
                    resume_text=resume,
                )
            )
        session.commit()

        employer = session.exec(
            select(User).where(User.email == "employer@example.com")
        ).one()
        employer2 = session.exec(
            select(User).where(User.email == "employer2@example.com")
        ).one()

        session.add_all(
            [
                Listing(
                    employer_id=employer.id,
                    title="Junior Software Engineer",
                    company="Acme Soft",
                    description="Build APIs and small UIs.",
                    apply_mode="collect",
                    external_url=None,
                    deadline="2099-12-31",
                    status="published",
                ),
                Listing(
                    employer_id=employer.id,
                    title="QA Intern",
                    company="Acme Soft",
                    description="Manual + light automation.",
                    apply_mode="external",
                    external_url="https://example.com/apply/qa",
                    deadline="2099-06-30",
                    status="pending",
                ),
                Listing(
                    employer_id=employer2.id,
                    title="Expired Analyst Role",
                    company="PastCo",
                    description="Should not appear after deadline.",
                    apply_mode="collect",
                    external_url=None,
                    deadline="2020-01-01",
                    status="published",
                ),
            ]
        )
        session.commit()

        grad = session.exec(
            select(User).where(User.email == "grad.dcit@example.com")
        ).one()
        session.add(Subscription(graduate_id=grad.id))
        session.commit()
