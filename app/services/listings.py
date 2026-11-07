"""Listing submit / publish / browse helpers."""

from __future__ import annotations

from typing import Any

from sqlmodel import Session, select

from app.database import engine
from app.models.listing import Listing
from app.models.notification import Notification
from app.models.subscription import Subscription
from app.services.board_auth import get_user

ELIGIBLE_PROGRAMMES = {"DCIT"}


def subscribe(graduate_id: int) -> dict[str, Any]:
    user = get_user(graduate_id)
    if not user or user["role"] != "graduate":
        return {"ok": False, "error": "graduates only"}
    # DEFECT: no programme eligibility check
    with Session(engine) as session:
        existing = session.exec(
            select(Subscription).where(Subscription.graduate_id == graduate_id)
        ).one_or_none()
        if existing is None:
            session.add(Subscription(graduate_id=graduate_id))
            session.commit()
    return {"ok": True}


def list_jobs_for_graduates() -> list[dict[str, Any]]:
    with Session(engine) as session:
        # DEFECT: returns pending + expired listings
        rows = session.exec(select(Listing).order_by(Listing.id)).all()
        return [r.model_dump() for r in rows]


def list_pending_for_admin() -> list[dict[str, Any]]:
    with Session(engine) as session:
        rows = session.exec(
            select(Listing).where(Listing.status == "pending").order_by(Listing.id)
        ).all()
        return [r.model_dump() for r in rows]


def submit_listing(
    employer_id: int,
    title: str,
    company: str,
    description: str,
    apply_mode: str,
    deadline: str,
    external_url: str | None = None,
) -> dict[str, Any]:
    user = get_user(employer_id)
    if not user or user["role"] != "employer":
        return {"ok": False, "error": "employers only"}
    if apply_mode not in {"collect", "external"}:
        return {"ok": False, "error": "apply_mode must be collect|external"}
    if apply_mode == "external" and not external_url:
        return {"ok": False, "error": "external_url required"}

    # DEFECT: published immediately (skip pending/admin)
    status = "published"
    with Session(engine) as session:
        listing = Listing(
            employer_id=employer_id,
            title=title,
            company=company,
            description=description,
            apply_mode=apply_mode,
            external_url=external_url,
            deadline=deadline,
            status=status,
        )
        session.add(listing)
        session.commit()
        session.refresh(listing)
        return {"ok": True, "listing_id": listing.id, "status": status}


def publish_listing(admin_id: int, listing_id: int) -> dict[str, Any]:
    admin = get_user(admin_id)
    if not admin or admin["role"] != "admin":
        return {"ok": False, "error": "admin only"}
    with Session(engine) as session:
        listing = session.get(Listing, listing_id)
        if listing is None:
            return {"ok": False, "error": "listing not found"}
        listing.status = "published"
        session.add(listing)
        session.commit()
    # DEFECT: publish does not notify subscribers
    return {"ok": True, "notified": False}


def notify_subscribers(admin_id: int, listing_id: int) -> dict[str, Any]:
    admin = get_user(admin_id)
    if not admin or admin["role"] != "admin":
        return {"ok": False, "error": "admin only"}
    with Session(engine) as session:
        listing = session.get(Listing, listing_id)
        if listing is None:
            return {"ok": False, "error": "listing not found"}
        subs = session.exec(select(Subscription)).all()
        for sub in subs:
            session.add(
                Notification(
                    user_id=sub.graduate_id,
                    message=f"New job published: {listing.title} at {listing.company}",
                )
            )
        session.commit()
        return {"ok": True, "count": len(subs)}
