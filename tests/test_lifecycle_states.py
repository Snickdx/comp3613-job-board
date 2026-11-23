"""Unit tests for the State-pattern application lifecycle.

Covers every legal transition, every illegal transition, the final states,
the refusal of `reopen`, unknown actions, and flag/status consistency.
"""

import pytest

from app.services.application_states import (
    ApplicationStateFactory,
    InvalidTransitionError,
)
from app.services.lifecycle import (
    ACTIONS,
    apply_action,
    derived_status_from_flags,
)

STATUSES = ["submitted", "reviewed", "shortlisted", "rejected", "hired"]
ACTION_NAMES = ["mark_reviewed", "shortlist", "reject", "hire"]

# (status, action) -> new status. Everything else must be refused.
LEGAL = {
    ("submitted", "mark_reviewed"): "reviewed",
    ("reviewed", "shortlist"): "shortlisted",
    ("reviewed", "reject"): "rejected",
    ("shortlisted", "hire"): "hired",
    ("shortlisted", "reject"): "rejected",
}

FLAGS_FOR_STATUS = {
    "submitted": (0, 0, 0, 0),
    "reviewed": (1, 0, 0, 0),
    "shortlisted": (1, 1, 0, 0),
    "rejected": (1, 0, 1, 0),
    "hired": (1, 1, 0, 1),
}


def make_app(status: str) -> dict:
    reviewed, shortlisted, rejected, hired = FLAGS_FOR_STATUS[status]
    return {
        "id": 1,
        "status": status,
        "flag_reviewed": reviewed,
        "flag_shortlisted": shortlisted,
        "flag_rejected": rejected,
        "flag_hired": hired,
    }


@pytest.mark.parametrize("status", STATUSES)
def test_factory_returns_state_with_matching_name(status):
    assert ApplicationStateFactory.from_status(status).name == status


def test_factory_rejects_unknown_status():
    with pytest.raises(InvalidTransitionError):
        ApplicationStateFactory.from_status("archived")


@pytest.mark.parametrize(("status", "action"), list(LEGAL))
def test_legal_transitions_succeed(status, action):
    result = apply_action(make_app(status), action)
    assert result["ok"] is True
    assert result["changed"] is True
    assert result["application"]["status"] == LEGAL[(status, action)]
    assert result["row"]["status"] == LEGAL[(status, action)]


ILLEGAL = [
    (status, action)
    for status in STATUSES
    for action in ACTION_NAMES
    if (status, action) not in LEGAL
]


@pytest.mark.parametrize(("status", "action"), ILLEGAL)
def test_illegal_transitions_are_refused(status, action):
    app = make_app(status)
    before = dict(app)
    result = apply_action(app, action)
    assert result["ok"] is False
    assert result["code"] == "invalid_transition"
    assert "row" not in result
    assert app == before  # the application is left unchanged


@pytest.mark.parametrize(
    ("status", "action"),
    [
        ("submitted", "shortlist"),
        ("submitted", "hire"),
        ("reviewed", "hire"),
    ],
)
def test_skipping_a_stage_is_refused(status, action):
    assert apply_action(make_app(status), action)["ok"] is False


@pytest.mark.parametrize(
    ("status", "action"),
    [
        ("reviewed", "mark_reviewed"),
        ("shortlisted", "mark_reviewed"),
        ("shortlisted", "shortlist"),
    ],
)
def test_moving_backwards_or_repeating_is_refused(status, action):
    assert apply_action(make_app(status), action)["ok"] is False


@pytest.mark.parametrize("status", ["rejected", "hired"])
@pytest.mark.parametrize("action", ACTIONS)
def test_final_states_refuse_every_action(status, action):
    result = apply_action(make_app(status), action)
    assert result["ok"] is False
    assert result["code"] == "invalid_transition"


@pytest.mark.parametrize("status", STATUSES)
def test_reopen_is_always_refused(status):
    result = apply_action(make_app(status), "reopen")
    assert result["ok"] is False
    assert result["code"] == "invalid_transition"


def test_unknown_action_is_refused():
    result = apply_action(make_app("submitted"), "promote")
    assert result["ok"] is False
    assert result["code"] == "unknown_action"


def test_full_happy_path_to_hired():
    app = make_app("submitted")
    for action, expected in [
        ("mark_reviewed", "reviewed"),
        ("shortlist", "shortlisted"),
        ("hire", "hired"),
    ]:
        result = apply_action(app, action)
        assert result["ok"] is True
        app = result["row"]
        assert app["status"] == expected


def test_full_path_to_rejected():
    app = make_app("submitted")
    for action in ["mark_reviewed", "reject"]:
        result = apply_action(app, action)
        assert result["ok"] is True
        app = result["row"]
    assert app["status"] == "rejected"


@pytest.mark.parametrize(("status", "action"), list(LEGAL))
def test_status_and_flags_agree_after_every_legal_move(status, action):
    result = apply_action(make_app(status), action)
    row = result["row"]
    assert derived_status_from_flags(row) == row["status"]
    assert result["application"]["status"] == row["status"]


def test_rejected_after_shortlisted_clears_no_history_and_sets_rejected():
    result = apply_action(make_app("shortlisted"), "reject")
    row = result["row"]
    assert row["flag_rejected"] == 1
    assert row["flag_hired"] == 0
    assert derived_status_from_flags(row) == "rejected"
