"""Application create / read / status transitions via lifecycle tracker."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlmodel import Session, select

from app.database import engine
from app.models.application import Application
from app.models.listing import Listing
from app.services.board_auth import get_user
from app.services.lifecycle import ACTIONS, apply_action


def apply(
    graduate_id: int,
    listing_id: int,
    cover_letter: str,
    resume_text: str | None = None,
) -> dict[str, Any]:
    user = get_user(graduate_id)
    if not user or user["role"] != "graduate":
        return {"ok": False, "error": "graduates only"}
    if user.get("programme") != "DCIT":
        return {"ok": False, "error": "DCIT graduates only"}

    with Session(engine) as session:
        listing = session.get(Listing, listing_id)
        if listing is None:
            return {"ok": False, "error": "listing not found"}
        if listing.status != "published":
            return {"ok": False, "error": "listing not published"}
        if listing.deadline < date.today().isoformat():
            return {"ok": False, "error": "listing expired"}
        if listing.apply_mode == "external":
            return {"ok": False, "error": "external listing; apply externally"}

        resume = resume_text or user.get("resume_text") or ""
        application = Application(
            listing_id=listing_id,
            graduate_id=graduate_id,
            cover_letter=cover_letter,
            resume_text=resume,
            status="submitted",
            flag_reviewed=0,
            flag_shortlisted=0,
            flag_rejected=0,
            flag_hired=0,
        )
        session.add(application)
        session.commit()
        session.refresh(application)
        return {
            "ok": True,
            "application_id": application.id,
            "status": "submitted",
        }


def my_applications(graduate_id: int) -> list[dict[str, Any]]:
    """Graduates always see the single canonical status column."""
    with Session(engine) as session:
        rows = session.exec(
            select(Application)
            .where(Application.graduate_id == graduate_id)
            .order_by(Application.id)
        ).all()
        return [row.model_dump() for row in rows]


def listing_applicants(viewer_id: int, listing_id: int) -> dict[str, Any]:
    viewer = get_user(viewer_id)
    if not viewer:
        return {"ok": False, "error": "unknown user"}
    with Session(engine) as session:
        listing = session.get(Listing, listing_id)
        if listing is None:
            return {"ok": False, "error": "listing not found"}
        if viewer["role"] not in {"employer", "admin"}:
            return {"ok": False, "error": "forbidden"}
        # Employers may only see applicants of their own listings.
        if viewer["role"] == "employer" and listing.employer_id != viewer_id:
            return {"ok": False, "error": "forbidden"}
        rows = session.exec(
            select(Application)
            .where(Application.listing_id == listing_id)
            .order_by(Application.id)
        ).all()
        return {"ok": True, "applicants": [r.model_dump() for r in rows]}


def export_applicants(admin_id: int, listing_id: int) -> dict[str, Any]:
    admin = get_user(admin_id)
    if not admin or admin["role"] != "admin":
        return {"ok": False, "error": "admin only"}
    result = listing_applicants(admin_id, listing_id)
    if not result.get("ok"):
        return result
    return {"ok": True, "format": "json", "package": result["applicants"]}


def transition_application(
    actor_id: int, application_id: int, action: str
) -> dict[str, Any]:
    """Change an application's status through the State-pattern lifecycle.

    Only the employer who owns the listing may do this. Administrators and
    other employers are refused. Every failure carries a `code` that the
    route maps to an HTTP status.
    """
    actor = get_user(actor_id)
    if not actor:
        return {"ok": False, "code": "unauthorized", "error": "unknown user"}
    if actor["role"] != "employer":
        return {"ok": False, "code": "forbidden", "error": "forbidden"}
    if action not in ACTIONS:
        return {
            "ok": False,
            "code": "invalid_transition",
            "error": f"cannot perform {action}; action must be one of {ACTIONS}",
        }

    with Session(engine) as session:
        row = session.get(Application, application_id)
        if row is None:
            return {
                "ok": False,
                "code": "not_found",
                "error": "application not found",
            }

        listing = session.get(Listing, row.listing_id)
        if listing is None or listing.employer_id != actor_id:
            return {"ok": False, "code": "forbidden", "error": "forbidden"}

        result = apply_action(row, action)
        if not result.get("ok"):
            return result

        session.add(row)
        session.commit()
        session.refresh(row)
        return {"ok": True, "application": row.model_dump(), "changed": True}
