"""Application create / read / status transitions via lifecycle tracker."""

from __future__ import annotations

from typing import Any

from sqlmodel import Session, select

from app.database import engine
from app.models.application import Application
from app.models.listing import Listing
from app.services.board_auth import get_user
from app.services.lifecycle import ACTIONS, apply_action
from app.services.listings import is_eligible_graduate, is_open_to_graduates


def apply(
    graduate_id: int,
    listing_id: int,
    cover_letter: str,
    resume_text: str | None = None,
) -> dict[str, Any]:
    user = get_user(graduate_id)
    if not user or user["role"] != "graduate":
        return {"ok": False, "error": "graduates only"}
    if not is_eligible_graduate(user):
        return {"ok": False, "error": "only eligible programme graduates may apply"}

    with Session(engine) as session:
        listing = session.get(Listing, listing_id)
        if listing is None or not is_open_to_graduates(listing):
            return {"ok": False, "error": "listing not found or no longer open"}

        # AC 13: external listings must not create an Application row.
        if listing.apply_mode == "external":
            return {
                "ok": False,
                "error": "this listing takes applications externally",
                "external_url": listing.external_url,
            }
        resume = resume_text or user.get("resume_text") or ""
        application = Application(
            listing_id=listing_id,
            graduate_id=graduate_id,
            cover_letter=cover_letter,
            resume_text=resume,
            status="submitted",
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
    with Session(engine) as session:
        rows = session.exec(
            select(Application)
            .where(Application.graduate_id == graduate_id)
            .order_by(Application.id)
        ).all()
        results = []
        for row in rows:
            results.append(row.model_dump())
        return results


def listing_applicants(viewer_id: int, listing_id: int) -> dict[str, Any]:
    viewer = get_user(viewer_id)
    if not viewer:
        return {"ok": False, "error": "unknown user"}
    with Session(engine) as session:
        listing = session.get(Listing, listing_id)
        if listing is None:
            return {"ok": False, "error": "listing not found"}
        # DEFECT (IDOR): ownership not checked for employers
        if viewer["role"] not in {"employer", "admin"}:
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
    """Drive the poorly factored lifecycle module."""
    actor = get_user(actor_id)
    if not actor:
        return {"ok": False, "error": "unknown user"}
    # DEFECT: admin may transition; any employer may transition any application
    if actor["role"] not in {"employer", "admin"}:
        return {"ok": False, "error": "forbidden"}
    if action not in ACTIONS:
        return {"ok": False, "error": f"action must be one of {ACTIONS}"}

    with Session(engine) as session:
        row = session.get(Application, application_id)
        if row is None:
            return {"ok": False, "error": "application not found"}

        result = apply_action(row.model_dump(), action)
        if not result.get("ok"):
            return result
        if not result.get("changed"):
            return {
                "ok": True,
                "application": result["application"],
                "changed": False,
            }

        updated = result["row"]
        row.status = updated["status"]
        session.add(row)
        session.commit()
        session.refresh(row)
        return {"ok": True, "application": row.model_dump(), "changed": True}
