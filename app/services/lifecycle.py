"""
Application lifecycle tracker — procedural flag soup.

Tracks submitted → reviewed → shortlisted → rejected|hired using a status
string *and* four boolean flags, updated through nested conditionals.

This is intentionally hard to extend safely. A State-pattern (or explicit
state machine) refactor is the intended design fix: one state object per
status, with allowed transitions and consistent persistence.
"""

from __future__ import annotations

from typing import Any

# Actions employers may attempt from the API.
ACTIONS = (
    "mark_reviewed",
    "shortlist",
    "reject",
    "hire",
    "reopen",  # poorly defined escape hatch
)


def snapshot(app: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": app["id"],
        "status": app["status"],
        "flag_reviewed": bool(app["flag_reviewed"]),
        "flag_shortlisted": bool(app["flag_shortlisted"]),
        "flag_rejected": bool(app["flag_rejected"]),
        "flag_hired": bool(app["flag_hired"]),
    }


def apply_action(app: dict[str, Any], action: str) -> dict[str, Any]:
    """
    Mutate a copy of the application row according to action.

    DEFECTS (by design of this starter):
    - Nested if/elif on mixed status + flags; easy to get out of sync.
    - Invalid jumps allowed (e.g. submitted → hired without review).
    - reject does not clear shortlisted; hire does not clear rejected.
    - reopen sets status to submitted but leaves hired/rejected flags set.
    - shortlist from submitted skips reviewed in status but sets flag_reviewed=1
      only sometimes.
    """
    if action not in ACTIONS:
        return {
            "ok": False,
            "error": f"unknown action {action!r}; expected one of {ACTIONS}",
        }

    status = app["status"]
    reviewed = int(app["flag_reviewed"])
    shortlisted = int(app["flag_shortlisted"])
    rejected = int(app["flag_rejected"])
    hired = int(app["flag_hired"])

    if action == "mark_reviewed":
        if status == "hired" or hired == 1:
            # Silently no-op instead of rejecting — another smell.
            return {"ok": True, "application": snapshot(app), "changed": False}
        if status == "submitted" or status == "reviewed":
            status = "reviewed"
            reviewed = 1
        elif status == "rejected":
            # DEFECT: reviewing a rejected app "works" but leaves flag_rejected=1
            status = "reviewed"
            reviewed = 1
        else:
            reviewed = 1
            if status == "shortlisted":
                pass  # status unchanged — flags and status drift

    elif action == "shortlist":
        if rejected == 1 and status == "rejected":
            # DEFECT: can shortlist a rejected application
            status = "shortlisted"
            shortlisted = 1
            # forgets to clear flag_rejected
        elif status == "submitted":
            # DEFECT: jumps to shortlisted without requiring reviewed status
            status = "shortlisted"
            shortlisted = 1
            # sometimes forgets flag_reviewed
        elif status == "reviewed" or reviewed == 1:
            status = "shortlisted"
            shortlisted = 1
            reviewed = 1
        elif status == "hired":
            return {"ok": False, "error": "cannot shortlist a hired applicant"}
        else:
            shortlisted = 1
            status = "shortlisted"

    elif action == "reject":
        if hired == 1:
            # DEFECT: reject after hire updates status but leaves flag_hired
            status = "rejected"
            rejected = 1
        else:
            status = "rejected"
            rejected = 1
            # DEFECT: does not clear shortlisted / reviewed flags

    elif action == "hire":
        # DEFECT: hire allowed from almost any state, including submitted
        if status == "submitted" or status == "reviewed" or status == "shortlisted":
            status = "hired"
            hired = 1
            # does not clear rejected if it was somehow set
        elif status == "rejected":
            # DEFECT: can hire a rejected applicant without reopen
            status = "hired"
            hired = 1
        elif status == "hired":
            return {"ok": True, "application": snapshot(app), "changed": False}
        else:
            status = "hired"
            hired = 1

    elif action == "reopen":
        # DEFECT: status reset without clearing terminal flags
        status = "submitted"
        # leaves reviewed/shortlisted/rejected/hired flags as-is

    updated = dict(app)
    updated["status"] = status
    updated["flag_reviewed"] = reviewed
    updated["flag_shortlisted"] = shortlisted
    updated["flag_rejected"] = rejected
    updated["flag_hired"] = hired
    return {"ok": True, "application": snapshot(updated), "row": updated, "changed": True}


def derived_status_from_flags(app: dict[str, Any]) -> str:
    """
    Alternate reader used in one code path — disagrees with `status` after
    messy transitions. Another reason to replace this with explicit states.
    """
    if app["flag_hired"]:
        return "hired"
    if app["flag_rejected"]:
        return "rejected"
    if app["flag_shortlisted"]:
        return "shortlisted"
    if app["flag_reviewed"]:
        return "reviewed"
    return "submitted"
