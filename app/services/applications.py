"""Application create / read / state transitions."""

from __future__ import annotations
from datetime import date
from typing import Any
from sqlmodel import Session, select
from app.database import engine

from app.models.application import Application
from app.models.listing import Listing
from app.models.graduate import Graduate
from app.models.employer import Employer
from app.models.admin import Admin

EMPLOYER_ACTIONS = {"review", "shortlist", "reject", "hire"}


def apply(
    graduate_id: int,
    listing_id: int,
    cover_letter: str,
    resume_text: str | None = None,
) -> dict[str, Any]:

    with Session(engine) as session:

        graduate = session.get(Graduate, graduate_id)
        if graduate is None:
            return {"ok": False, "error": "graduate not found"}
        if graduate.programme not in {"DCIT"}:
            return {"ok": False, "error": "graduate is not eligible"}

        listing = session.get(Listing, listing_id)
        if listing is None:
            return {"ok": False, "error": "listing not found"}
        if listing.apply_mode != "collect":
            return {"ok": False, "error": "external listings cannot accept on-platform applications"}
        if listing.status != "published":
            return {"ok": False, "error": "listing is not available"}
        try:
            deadline = date.fromisoformat(listing.deadline)
        except (TypeError, ValueError):
            return {"ok": False, "error": "listing has an invalid deadline"}
        if deadline < date.today():
            return {"ok": False, "error": "listing deadline has passed"}

        resume = resume_text or graduate.resume_text or ""
        if not cover_letter or not cover_letter.strip():
            return {"ok": False, "error": "cover letter is required"}
        if not resume or not resume.strip():
            return {"ok": False, "error": "resume is required"}

        application = Application(
            listing_id=listing_id,
            graduate_id=graduate_id,
            cover_letter=cover_letter,
            resume_text=resume,
            state="submitted",
        )

        session.add(application)
        session.commit()
        session.refresh(application)

        return {
            "ok": True,
            "application_id": application.id,
            "state": application.state,
        }


def my_applications(graduate_id: int) -> list[dict[str, Any]]:

    with Session(engine) as session:

        graduate = session.get(Graduate, graduate_id)
        if graduate is None:
            return []

        applications = session.exec(
            select(Application)
            .where(Application.graduate_id == graduate_id)
            .order_by(Application.id)
        ).all()

        application_rows = []
        for application in applications:
            row = application.model_dump()
            listing = session.get(Listing, application.listing_id)
            row["listing_title"] = listing.title if listing else "Listing unavailable"
            row["listing_company"] = listing.company if listing else ""
            application_rows.append(row)

        return application_rows


def listing_applicants(employer_id: int, listing_id: int) -> dict[str, Any]:

    with Session(engine) as session:

        employer = session.get(Employer, employer_id)
        if employer is None:
            return {"ok": False, "error": "employer not found"}

        listing = session.get(Listing, listing_id)
        if listing is None:
            return {"ok": False, "error": "listing not found"}

        if listing.employer_id != employer_id:
            return {"ok": False, "error": "forbidden"}

        applications = session.exec(
            select(Application)
            .where(Application.listing_id == listing_id)
            .order_by(Application.id)
        ).all()

        return {"ok": True, "applicants": [application.model_dump() for application in applications]}


def export_applicants(
        employer_id: int,
        listing_id: int
) -> dict[str, Any]:

    result = listing_applicants(employer_id, listing_id)
    if not result.get("ok"):
        return result

    return {"ok": True, "format": "json", "package": result["applicants"]}

def export_applicants_admin(
    listing_id: int
) -> dict[str, Any]:

    with Session(engine) as session:

        listing = session.get(Listing, listing_id)

        if listing is None:
            return {
                "ok": False,
                "error": "listing not found"
            }

        applicants = session.exec(
            select(Application)
            .where(Application.listing_id == listing_id)
            .order_by(Application.id)
        ).all()

        return {
            "ok": True,
            "format": "json",
            "package": [
                applicant.model_dump()
                for applicant in applicants
            ]
        }

def transition_application(
    actor_id: int,
    application_id: int,
    action: str,
) -> dict[str, Any]:

    with Session(engine) as session:

        application = session.get(Application, application_id)

        if application is None:
            return {
                "ok": False,
                "error": "application not found"
            }

        # Derive the role from role tables rather than a caller-supplied role.
        role_rows = sum(
            session.get(model, actor_id) is not None
            for model in (Graduate, Employer, Admin)
        )
        employer = session.get(Employer, actor_id)
        if role_rows != 1 or employer is None:
            return {"ok": False, "error": "forbidden"}

        listing = session.get(Listing, application.listing_id)
        if listing is None:
            return {"ok": False, "error": "listing not found"}
        if listing.employer_id != employer.id:
            return {"ok": False, "error": "forbidden"}

        if action not in EMPLOYER_ACTIONS:
            return {"ok": False, "error": "forbidden"}

        if not application.transition(action):
            return {
                "ok": False,
                "error": "invalid application state transition"
            }

        session.add(application)
        session.commit()
        session.refresh(application)

        return {
            "ok": True,
            "application": application.model_dump(),
            "changed": True
        }