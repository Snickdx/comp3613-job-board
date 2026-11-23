"""Job-board scenario JSON API (OpenAPI /docs)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException , Response 
from pydantic import BaseModel, Field

from app.dependencies.auth import AuthDep , AdminDep
from app.services import applications, listings
from app.services import board_auth as auth
from app.utilities.security import access_token_cookie_kwargs, create_access_token

router = APIRouter(tags=["job-board"])

ERROR_STATUS = {
    "invalid_action": 400,
    "forbidden": 403,
    "not_found": 404,
    "illegal_transition": 409,
}


def raise_for_error(result, default=400):
    raise HTTPException(
        status_code=ERROR_STATUS.get(result.get("code"), default),
        detail=result.get("error"),
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


class ApplyBody(BaseModel):
    listing_id: int
    cover_letter: str
    resume_text: str | None = None


class TransitionBody(BaseModel):
    action: str = Field(
        description="review | mark_reviewed | shortlist | reject | hire | reopen"
    )


@router.post("/auth/login")
def login(body: LoginBody, response: Response) -> dict[str, Any]:
    user = auth.login(body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="invalid credentials")

    token = create_access_token(
        data={"sub": str(user["id"]), "role": user["role"]}
    )
    response.set_cookie(
        key="access_token",
        value=token,
        **access_token_cookie_kwargs(),
    )
    return {"user": user}

@router.post("/graduates/subscribe")
def subscribe(user: AuthDep) -> dict[str, Any]:
    result = listings.subscribe(user.id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/jobs")
def jobs() -> dict[str, Any]:
    return {"jobs": listings.list_jobs_for_graduates()}

@router.get("/admin/listings/pending")
def pending(user: AdminDep) -> dict[str, Any]:
    return {"listings": listings.list_pending_for_admin()}


@router.post("/employer/listings")
def submit_listing(user: AuthDep, body: ListingBody) -> dict[str, Any]:
    result = listings.submit_listing(
        user.id,
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
def publish(listing_id: int, user: AdminDep) -> dict[str, Any]:
    result = listings.publish_listing(user.id, listing_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@router.post("/admin/listings/{listing_id}/notify")
def notify(listing_id: int, user: AdminDep) -> dict[str, Any]:
    result = listings.notify_subscribers(user.id, listing_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@router.post("/graduates/applications")
def apply(user: AuthDep, body: ApplyBody) -> dict[str, Any]:
    result = applications.apply(
        user.id, body.listing_id, body.cover_letter, body.resume_text
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/graduates/applications")
def my_apps(user: AuthDep) -> dict[str, Any]:
    return {"applications": applications.my_applications(user.id)}


@router.get("/listings/{listing_id}/applicants")
def applicants(listing_id: int, user: AuthDep) -> dict[str, Any]:
    result = applications.listing_applicants(user.id, listing_id)
    if not result.get("ok"):
        raise_for_error(result)
    return result


@router.get("/admin/listings/{listing_id}/export")
def export(listing_id: int, user : AdminDep) -> dict[str, Any]:
    result = applications.export_applicants(user.id, listing_id)
    if not result.get("ok"):
        raise_for_error(result)
    return result

@router.post("/applications/{application_id}/transition")
def transition(
    application_id: int, user: AuthDep, body: TransitionBody
) -> dict[str, Any]:
    result = applications.transition_application(
        user.id, application_id, body.action
    )
    if not result.get("ok"):
        raise_for_error(result)
    return result