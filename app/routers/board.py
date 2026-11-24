"""Job-board scenario JSON API (OpenAPI /docs)."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import applications, listings
from app.services import board_auth as auth
from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.models.graduate import Graduate
from app.models.employer import Employer
from app.models.admin import Admin


router = APIRouter(tags=["job-board"])

def require_graduate(current_user: AuthDep, db: SessionDep):
    graduate = db.get(Graduate, current_user.id)
    employer = db.get(Employer, current_user.id)
    admin = db.get(Admin, current_user.id)

    if graduate is None or employer is not None or admin is not None:
        raise HTTPException(
            status_code=403,
            detail="Graduate access required"
        )

    return graduate


def require_employer(current_user: AuthDep, db: SessionDep):
    employer = db.get(Employer, current_user.id)
    graduate = db.get(Graduate, current_user.id)
    admin = db.get(Admin, current_user.id)

    if employer is None or graduate is not None or admin is not None:
        raise HTTPException(
            status_code=403,
            detail="Employer access required"
        )

    return employer


def require_admin(current_user: AuthDep, db: SessionDep):
    admin = db.get(Admin, current_user.id)
    graduate = db.get(Graduate, current_user.id)
    employer = db.get(Employer, current_user.id)

    if admin is None or graduate is not None or employer is not None:
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )

    return admin


def handle_application_error(result: dict):
    if result.get("ok"):
        return result

    error = result.get("error", "request failed")

    if error == "forbidden":
        code = 403
    elif error == "graduate is not eligible":
        code = 403
    elif error.endswith("not found"):
        code = 404
    elif error in {
        "invalid application state transition",
        "listing is not available",
        "listing deadline has passed",
        "external listings cannot accept on-platform applications",
    }:
        code = 409
    elif error in {
        "listing has an invalid deadline",
        "cover letter is required",
        "resume is required",
    }:
        code = 422
    else:
        code = 400

    raise HTTPException(
        status_code=code,
        detail=error
    )


class LoginBody(BaseModel):
    email: str
    password: str


class ListingBody(BaseModel):
    title: str
    company: str
    description: str
    apply_mode: str = Field(description="collect | external")
    deadline: str = Field(description="ISO date YYYY-MM-DD")
    external_url: str | None = None
    actor_id: int = Field(description="Acting user id (demo auth)")


class ActorBody(BaseModel):
    actor_id: int


class ApplyBody(BaseModel):
    listing_id: int
    cover_letter: str = Field(min_length=1)
    resume_text: str | None = None


class TransitionBody(BaseModel):
    action: Literal["review", "shortlist", "reject", "hire"] = Field(
        description="review | shortlist | reject | hire"
    )


@router.post("/auth/login")
def login(body: LoginBody) -> dict[str, Any]:
    user = auth.login(body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="invalid credentials")
    return {"user": user}


@router.post("/graduates/subscribe")
def subscribe(body: ActorBody) -> dict[str, Any]:
    result = listings.subscribe(body.actor_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/jobs")
def jobs() -> dict[str, Any]:
    return {"jobs": listings.list_jobs_for_graduates()}


@router.get("/admin/listings/pending")
def pending(actor_id: int) -> dict[str, Any]:
    result = listings.list_pending_for_admin(actor_id)
    if not result.get("ok"):
        raise HTTPException(status_code=403, detail=result.get("error"))

    return result


@router.post("/employer/listings")
def submit_listing(body: ListingBody) -> dict[str, Any]:
    result = listings.submit_listing(
        body.actor_id,
        body.title,
        body.company,
        body.description,
        body.apply_mode,
        body.deadline,
        body.external_url,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/admin/listings/{listing_id}/publish")
def publish(listing_id: int, body: ActorBody) -> dict[str, Any]:
    result = listings.publish_listing(body.actor_id, listing_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/admin/listings/{listing_id}/notify")
def notify(listing_id: int, body: ActorBody) -> dict[str, Any]:
    result = listings.notify_subscribers(body.actor_id, listing_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/graduates/applications")
def apply(
    body: ApplyBody,
    current_user: AuthDep,
    db: SessionDep
) -> dict[str, Any]:

    graduate = require_graduate(current_user, db)

    result = applications.apply(
        graduate.id,
        body.listing_id,
        body.cover_letter,
        body.resume_text
    )

    return handle_application_error(result)


@router.get("/graduates/applications")
def my_apps(
    current_user: AuthDep,
    db: SessionDep
) -> dict[str, Any]:

    graduate = require_graduate(current_user, db)

    return {
        "applications": applications.my_applications(
            graduate.id
        )
    }


@router.get("/listings/{listing_id}/applicants")
def applicants(
    listing_id: int,
    current_user: AuthDep,
    db: SessionDep
) -> dict[str, Any]:

    employer = require_employer(current_user, db)

    result = applications.listing_applicants(
        employer.id,
        listing_id
    )

    return handle_application_error(result)


@router.get("/admin/listings/{listing_id}/export")
def export(
    listing_id: int,
    current_user: AuthDep,
    db: SessionDep
) -> dict[str, Any]:

    require_admin(current_user, db)

    result = applications.export_applicants_admin(
        listing_id
    )

    return handle_application_error(result)


@router.post("/applications/{application_id}/transition")
def transition(
    application_id: int,
    body: TransitionBody,
    current_user: AuthDep,
    db: SessionDep
) -> dict[str, Any]:

    employer = db.get(Employer, current_user.id)
    graduate = db.get(Graduate, current_user.id)
    admin = db.get(Admin, current_user.id)

    role_count = sum(
        role is not None
        for role in (employer, graduate, admin)
    )
    if role_count != 1 or employer is None:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to change application status"
        )

    result = applications.transition_application(
        actor_id=current_user.id,
        application_id=application_id,
        action=body.action,
    )

    return handle_application_error(result)