"""Listing submit / publish / browse helpers."""

from __future__ import annotations
from typing import Any
from sqlmodel import Session, select
from app.database import engine

from app.models.listing import Listing
from app.models.notification import Notification
from app.models.subscription import Subscription
from app.models.graduate import Graduate
from app.models.employer import Employer
from app.models.admin import Admin

ELIGIBLE_PROGRAMMES = {"DCIT"}


def subscribe(graduate_id: int) -> dict[str, Any]:

    with Session(engine) as session:

        graduate = session.get(Graduate, graduate_id)
        if graduate is None:
            return {"ok": False, "error": "graduate not found"}

        if graduate.programme not in ELIGIBLE_PROGRAMMES:
            return {"ok": False, "error": "graduate is not eligible"}

        existing = session.exec(
            select(Subscription)
            .where(Subscription.graduate_id == graduate_id)
        ).one_or_none()

        if existing is None:
            session.add(Subscription(graduate_id=graduate_id))
            session.commit()

        return {"ok": True}


def list_jobs_for_graduates() -> list[dict[str, Any]]:

    with Session(engine) as session:

        rows = session.exec(
            select(Listing)
            .where(Listing.status == "published")
            .order_by(Listing.id)
        ).all()

        return [row.model_dump() for row in rows]


def list_pending_for_admin(admin_id: int) -> list[dict[str, Any]]:

    with Session(engine) as session:

        admin = session.get(Admin, admin_id)
        if admin is None:
            return {"ok": False, "error": "admin not found"}
        
        rows = session.exec(
            select(Listing)
            .where(Listing.status == "pending")
            .order_by(Listing.id)
        ).all()

        return [row.model_dump() for row in rows]


def submit_listing(
    employer_id: int,
    title: str,
    company: str,
    description: str,
    apply_mode: str,
    deadline: str,
    external_url: str | None = None,
) -> dict[str, Any]:

    with Session(engine) as session:

        employer = session.get(Employer, employer_id)
        if employer is None:
            return {"ok": False, "error": "employer not found"}

        if apply_mode not in {"collect", "external"}:
            return {"ok": False, "error": "apply_mode must be collect|external"}

        if apply_mode == "external" and not external_url:
            return {"ok": False, "error": "external_url required"}

        status = "pending"

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


def publish_listing(
    admin_id: int,
    listing_id: int
) -> dict[str, Any]:

    with Session(engine) as session:

        admin = session.get(Admin, admin_id)
        if admin is None:
            return {"ok": False, "error": "admin not found"}

        listing = session.get(Listing, listing_id)
        if listing is None:
            return {"ok": False, "error": "listing not found"}

        if listing.status != "pending":
            return {"ok": False, "error": "only pending listings can be approved"}

        listing.status = "published"

        session.add(listing)
        session.commit()

        # maybe notify subscribers here

        return {"ok": True, "status": "published"}


def reject_listing(
    admin_id: int,
    listing_id: int,
) -> dict[str, Any]:

    with Session(engine) as session:

        admin = session.get(Admin, admin_id)
        if admin is None:
            return {"ok": False, "error": "admin not found"}

        listing = session.get(Listing, listing_id)
        if listing is None:
            return {"ok": False, "error": "listing not found"}
        
        if listing.status != "pending":
            return {"ok": False, "error": "only pending listings can be rejected"}
        
        listing.status = "rejected"
        
        session.add(listing)
        session.commit()
        
        return {"ok": True, "status": "rejected"}


def notify_subscribers(
    admin_id: int,
    listing_id: int
) -> dict[str, Any]:

    with Session(engine) as session:

        admin = session.get(Admin, admin_id)
        if admin is None:
            return {"ok": False, "error": "admin not found"}

        listing = session.get(Listing, listing_id)
        if listing is None:
            return {"ok": False, "error": "listing not found"}

        if listing.status != "published":
            return {"ok": False, "error": "only published listings can notify subscribers"}
                
        subscriptions = session.exec(select(Subscription)).all()
        for subscription in subscriptions:
            session.add(
                Notification(
                    user_id=subscription.graduate_id,
                    message=(
                        f"New job published: "
                        f"{listing.title} at {listing.company}"
                    ),
                )
            )
        session.commit()

        return {"ok": True, "count": len(subscriptions)}