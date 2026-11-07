"""Job-board scenario JSON API (OpenAPI /docs)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import applications, listings
from app.services import board_auth as auth

router = APIRouter(tags=["job-board"])


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
    cover_letter: str
    resume_text: str | None = None
    actor_id: int


class TransitionBody(BaseModel):
    action: str = Field(
        description="mark_reviewed | shortlist | reject | hire | reopen"
    )
    actor_id: int


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
    actor = auth.get_user(actor_id)
    if not actor or actor["role"] != "admin":
        raise HTTPException(status_code=403, detail="admin only")
    return {"listings": listings.list_pending_for_admin()}


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
def apply(body: ApplyBody) -> dict[str, Any]:
    result = applications.apply(
        body.actor_id, body.listing_id, body.cover_letter, body.resume_text
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/graduates/applications")
def my_apps(actor_id: int) -> dict[str, Any]:
    return {"applications": applications.my_applications(actor_id)}


@router.get("/listings/{listing_id}/applicants")
def applicants(listing_id: int, actor_id: int) -> dict[str, Any]:
    result = applications.listing_applicants(actor_id, listing_id)
    if not result.get("ok"):
        raise HTTPException(status_code=403, detail=result.get("error"))
    return result


@router.get("/admin/listings/{listing_id}/export")
def export(listing_id: int, actor_id: int) -> dict[str, Any]:
    result = applications.export_applicants(actor_id, listing_id)
    if not result.get("ok"):
        raise HTTPException(status_code=403, detail=result.get("error"))
    return result


@router.post("/applications/{application_id}/transition")
def transition(application_id: int, body: TransitionBody) -> dict[str, Any]:
    result = applications.transition_application(
        body.actor_id, application_id, body.action
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result
