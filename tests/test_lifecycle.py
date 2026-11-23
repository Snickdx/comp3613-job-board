import copy

import pytest

from app.services.lifecycle import (
    HiredState,
    RejectedState,
    ReviewedState,
    ShortlistedState,
    SubmittedState,
    apply_action,
    state_for,
)


def application(status: str) -> dict:
    return {
        "id": 1,
        "status": status,
        "flag_reviewed": 0,
        "flag_shortlisted": 0,
        "flag_rejected": 0,
        "flag_hired": 0,
    }


@pytest.mark.parametrize(
    ("start", "action", "expected"),
    [
        ("submitted", "mark_reviewed", "reviewed"),
        ("reviewed", "shortlist", "shortlisted"),
        ("reviewed", "reject", "rejected"),
        ("shortlisted", "reject", "rejected"),
        ("shortlisted", "hire", "hired"),
        ("rejected", "reopen", "submitted"),
    ],
)
def test_legal_transitions(start, action, expected):
    original = application(start)
    before = copy.deepcopy(original)

    result = apply_action(original, action)

    assert result["ok"] is True
    assert result["changed"] is True
    assert result["row"]["status"] == expected
    assert result["application"]["status"] == expected
    assert original == before


@pytest.mark.parametrize(
    ("start", "action"),
    [
        ("submitted", "shortlist"),
        ("submitted", "reject"),
        ("submitted", "hire"),
        ("submitted", "reopen"),
        ("reviewed", "mark_reviewed"),
        ("reviewed", "hire"),
        ("reviewed", "reopen"),
        ("shortlisted", "mark_reviewed"),
        ("shortlisted", "shortlist"),
        ("shortlisted", "reopen"),
        ("rejected", "mark_reviewed"),
        ("rejected", "shortlist"),
        ("rejected", "reject"),
        ("rejected", "hire"),
        ("hired", "mark_reviewed"),
        ("hired", "shortlist"),
        ("hired", "reject"),
        ("hired", "hire"),
        ("hired", "reopen"),
    ],
)
def test_illegal_transitions_are_rejected_without_mutation(start, action):
    original = application(start)
    before = copy.deepcopy(original)

    result = apply_action(original, action)

    assert result["ok"] is False
    assert "cannot" in result["error"]
    assert "changed" not in result
    assert original == before


@pytest.mark.parametrize("action", ["archive", "approve", "", "MARK_REVIEWED"])
def test_unknown_actions_are_rejected(action):
    original = application("submitted")
    before = copy.deepcopy(original)

    result = apply_action(original, action)

    assert result["ok"] is False
    assert "unknown action" in result["error"]
    assert original == before


@pytest.mark.parametrize(
    ("status", "state_type"),
    [
        ("submitted", SubmittedState),
        ("reviewed", ReviewedState),
        ("shortlisted", ShortlistedState),
        ("rejected", RejectedState),
        ("hired", HiredState),
    ],
)
def test_state_for_returns_concrete_state(status, state_type):
    assert isinstance(state_for(status), state_type)


def test_hired_is_terminal():
    original = application("hired")
    before = copy.deepcopy(original)

    for action in ("mark_reviewed", "shortlist", "reject", "hire", "reopen"):
        result = apply_action(original, action)
        assert result["ok"] is False

    assert original == before


def test_legacy_flags_do_not_change_status():
    original = application("submitted")
    original.update(
        {
            "flag_reviewed": 1,
            "flag_shortlisted": 1,
            "flag_rejected": 1,
            "flag_hired": 1,
        }
    )
    before = copy.deepcopy(original)

    result = apply_action(original, "mark_reviewed")

    assert result["ok"] is True
    assert result["row"]["status"] == "reviewed"
    assert original == before
