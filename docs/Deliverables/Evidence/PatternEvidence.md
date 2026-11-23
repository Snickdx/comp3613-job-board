# Sprint 2 #12 — Pattern Evidence: State pattern in the application lifecycle

This note shows that the State pattern described in the Sprint 1
[Pattern Rationale](../Requirements/PatternRationale.md) and
[class diagram](../diagrams/ClassDiagram/ClassDiagram_Sprint1.png) is now in the code.
It links each pattern role to a file and a PR, shows the before and after code, and lists the
tests that prove the inherited defects D1–D7 are fixed.

## 1. Pattern roles → code → PR

| Pattern role | Code | Sprint 2 card | PR |
|---|---|---|---|
| **State** (abstract) — every action raises `IllegalTransition` by default | `ApplicationState` in `app/services/application_states.py` | S2-#2 | #13 |
| **Concrete states** — each overrides only its legal moves | `SubmittedState`, `ReviewedState`, `ShortlistedState`, `RejectedState`, `HiredState` (same file) | S2-#2 | #13 |
| **Status → state lookup** | `STATES` dict and `state_for(status)` (same file) | S2-#2 | #13 |
| **Context** — loads the current state, delegates the action, returns the new status | `apply_action()` in `app/services/lifecycle.py` | S2-#5 | #19 |
| **Single source of truth** — the four `flag_*` columns are removed; `status` is the only lifecycle field | `Application` in `app/models/application.py` | S2-#4 | #15 |
| **Client** — checks ownership *before* asking the state to move, then saves | `transition_application()` in `app/services/applications.py` | S2-#5, S2-#7 | #19, #18 |
| **Error mapping** — `illegal_transition` → 409, `forbidden` → 403, `not_found` → 404, `invalid_action` → 400 | `ERROR_STATUS` in `app/routers/board.py` | S2-#8 | #17 |

## 2. Before and after

**Before (inherited, `app/services/lifecycle.py`).** The status was stored twice, as a string
and as four flags. One nested `if/elif` handled every action, and nothing defined which moves
were legal:

```python
reviewed = int(app["flag_reviewed"])
rejected = int(app["flag_rejected"])
...
elif status == "rejected":
    # DEFECT: reviewing a rejected app "works" but leaves flag_rejected=1
```

**After.** Each state knows only its own legal moves. Anything else falls through to the base
class and raises an error:

```python
class ShortlistedState(ApplicationState):
    status = "shortlisted"

    def hire(self) -> "HiredState":
        return HiredState()

    def reject(self) -> "RejectedState":
        return RejectedState()
```

```python
# lifecycle.py — the context delegates instead of branching
next_state = state_for(app["status"]).transition(action)
```

Adding a new stage, such as "interview scheduled", now means adding one class and changing
the states that lead to it. No existing `if/elif` chain has to be edited (Open/Closed Principle).

## 3. Transition rules as implemented

| From | Legal actions → To | Everything else |
|---|---|---|
| submitted | review / mark_reviewed → reviewed | 409 |
| reviewed | shortlist → shortlisted; reject → rejected | 409 |
| shortlisted | hire → hired; reject → rejected | 409 |
| rejected | reopen → reviewed (Employer interview, E3) | 409 |
| hired | none (final state) | 409 |

## 4. Defects fixed and the tests that prove it

| Defect | What was wrong | Fixed by | Test (`tests/test_regression.py`) |
|---|---|---|---|
| D1 | Hire allowed straight from submitted | `SubmittedState` has no `hire()` | `test_D1_hire_from_submitted_is_refused` |
| D2 | A rejected application could be shortlisted | `RejectedState` only allows `reopen()` | `test_D2_rejected_application_cannot_be_shortlisted` |
| D3 | Reopen left the old flags set | Flags removed; one `status` field | `test_D3_reopen_leaves_one_consistent_status` |
| D4 | Graduate (flags) and employer (status) saw different statuses | Both read `status` | `test_D4_graduate_and_employer_see_the_same_status` |
| D5 | Any employer could move any application | Ownership check before the state is called | `test_D5_only_listing_employer_can_transition` |
| D6 | Illegal action on a hired application returned OK | `IllegalTransition` → 409 | `test_D6_illegal_action_on_hired_is_an_error_not_silent_ok` |
| D7 | Response did not match what was stored | One response shape built from the saved row | `test_D7_transition_response_matches_stored_application` |

The pattern is also tested at two other levels:

- **Unit** (`tests/test_unit.py`, S2-#3, PR #14): every legal transition, every illegal
  transition from every state, unknown actions refused, and `Application` has no flag columns.
- **Integration** (`tests/test_integration.py`, S2-#6, PR #20): the owner drives the full
  lifecycle, a rejected application is reopened, an illegal transition is refused, and a
  non-owner or admin is refused.

## 5. Test run

Run on commit `06903a7` (merge of PR #21, the last commit before session auth was merged):

```
pytest -q --cov=app.services.application_states --cov=app.services.lifecycle
56 passed

app/services/application_states.py   96%
app/services/lifecycle.py            81%
TOTAL                                93%
```

Screenshots: [9-SC1](9_Regression_Tests/9-SC1.png) shows the regression test run from the S2-#9 PR, and
[9-SC2](9_Regression_Tests/9-SC2.png) shows the full suite (58 passed) after session auth (PR #25).

## 6. Differences from the Sprint 1 class diagram

The code follows the diagram's design, with these implementation differences:

| Sprint 1 diagram | Implemented | Reason |
|---|---|---|
| `ApplicationLifecycle` context class | `apply_action()` function in `lifecycle.py` | The codebase uses module-level service functions, not service classes |
| `status(): ApplicationStatus` method | `status` class attribute (string) | Simpler; the database stores a plain string |
| `ApplicationState.fromStatus()` static method | `state_for()` and a `STATES` dict | Same role: maps the stored status to its state object |
| `SubmittedState.review()` only | `review()` and `mark_reviewed()` | `mark_reviewed` is kept as an alias so the inherited API action still works |
| `ApplicationRepository` | Direct `Session` queries in the service | No repository layer exists for applications in the starter |

The class diagram has been updated to match these names (S2-#12, PR #23 and PR #26):
[plantuml-diagramSprint2.png](../diagrams/ClassDiagram/plantuml-diagramSprint2.png)
([source](../diagrams/ClassDiagram/class-diagram_Sprint2.puml)). The Sprint 1 version is kept as
[ClassDiagram_Sprint1.png](../diagrams/ClassDiagram/ClassDiagram_Sprint1.png) for comparison.
The pattern itself (five states, the legal transitions, `IllegalTransition`, one stored `status`)
is unchanged from the Sprint 1 design.
