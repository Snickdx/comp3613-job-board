# Sprint 2 Report — Implementation and Testing

**Project:** COMP 3613 Job Board  
**Special feature:** Application lifecycle and transitions  
**Design pattern:** State  
**Report date:** 2026-11-23

## Sprint 2 Summary

Sprint 2 implemented the State pattern for application lifecycle transitions and added unit, integration, and regression tests for the lifecycle and related job-board requirements. The pattern is part of the working application code, rather than only being documented as a design.

## Implementation — 20%

The special feature is implemented across the model, service, and API layers:

| Pattern responsibility | Implementation |
|---|---|
| State abstraction and legal transitions | `ApplicationState` and concrete lifecycle states in [`application_states.py`](../../../app/services/application_states.py) |
| Map stored status to a state | `STATES` and `state_for()` in [`application_states.py`](../../../app/services/application_states.py) |
| Delegate a lifecycle action | `apply_action()` in [`lifecycle.py`](../../../app/services/lifecycle.py) |
| Persist a valid transition and enforce ownership | `transition_application()` in [`applications.py`](../../../app/services/applications.py) |
| Return appropriate API errors | `ERROR_STATUS` and the transition route in [`board.py`](../../../app/routers/board.py) |
| Store one consistent lifecycle value | `Application.status` in [`application.py`](../../../app/models/application.py) |

The implemented transition rules are:

| Current state | Allowed actions | Result |
|---|---|---|
| submitted | `review`, `mark_reviewed` | reviewed |
| reviewed | `shortlist`, `reject` | shortlisted or rejected |
| shortlisted | `hire`, `reject` | hired or rejected |
| rejected | `reopen` | reviewed |
| hired | none | Final state |

Invalid transitions are rejected. The transition service checks listing ownership before applying a state change, so another employer or an administrator cannot transition an employer’s application.

The API maps errors to HTTP status codes: invalid action to 400, forbidden to 403, not found to 404, and illegal transition to 409.

The pattern implementation and its mapping to the Sprint 1 design are documented in [`PatternEvidence.md`](./PatternEvidence.md). The design rationale is in [`PatternRationale.md`](../Requirements/PatternRationale.md).

## Testing — 15%

Tests exercise the lifecycle at multiple levels:

- **Unit tests:** [`test_unit.py`](../../../tests/test_unit.py) covers legal and illegal transitions, unknown actions, lifecycle action handling, and the application model’s status field.
- **Integration tests:** [`test_integration.py`](../../../tests/test_integration.py) covers a full employer-owned lifecycle, reopening a rejected application, invalid transitions, and attempts by non-owners or administrators.
- **Regression tests:** [`test_regression.py`](../../../tests/test_regression.py) covers lifecycle defects D1–D7 and job-board authorization and eligibility defects.
- **Scenario tests:** [`test_scenario.py`](../../../tests/test_scenario.py) provides smoke tests for application health, API login, and job-list retrieval.

Current full-suite run (after S2-#13), recorded in [`Coverage_Report.md`](./Coverage_Report.md):

| Result | Value |
|---|---:|
| Tests passed | **61** (0 failed) |
| `application_states.py` (State pattern) | 96% |
| `applications.py` | 91% |
| `board.py` | 95% |
| `lifecycle.py` | 81% |
| `listings.py` | 90% |
| Whole `app/` folder | 32% |

The special feature is covered at 81–96%. The whole-app figure includes FastStart starter code the
team did not change (server configuration pages, PDF/transcript export, CLI, HTML page routes).

## Evidence

- Regression tests: [`9-SC1.png`](./9_Regression_Tests/9-SC1.png) (S2-#9), [`9-SC2.png`](./9_Regression_Tests/9-SC2.png) (full suite after session auth)
- Coverage: [`14-SC1.png`](./14_Coverage/14-SC1.png) and [`Coverage_Report.md`](./Coverage_Report.md)
- Fix evidence: [`10_Eligibility_Rules/`](./10_Eligibility_Rules/), [`8_Error_Status_Codes/`](./8_Error_Status_Codes/), [`7_listing-ownership/`](./7_listing-ownership/), [`13_Listing_Review/`](./13_Listing_Review/)
- State-pattern implementation details and defect-to-test mapping: [`PatternEvidence.md`](./PatternEvidence.md)
- Updated class diagram: [`ClassDiagram.png`](../diagrams/ClassDiagram/ClassDiagram.png) ([source](../diagrams/ClassDiagram/class-diagram.puml)); Sprint 1 version kept as [`ClassDiagram_Sprint1.png`](../diagrams/ClassDiagram/ClassDiagram_Sprint1.png)

## Planning (done at the beginning)

| Owner | Task Number & Title |
|---|---|
| Raiden | #1 Sprint 2 planning |
| Raiden | #2 State pattern classes |
| Raiden | #3 Unit tests for the states |
| Jelani | #4 Remove the status flags |
| Jelani | #5 Route transitions through the State pattern |
| Jelani | #6 Test database fixture + lifecycle integration tests |
| Cristian | #7 Listing ownership checks |
| Cristian | #8 Error-to-HTTP mapping |
| Cristian | #9 Regression tests for the audit defects |
| Cristian | #10 Eligibility and listing rules |
| Unassigned (stretch) | #11 Session auth instead of `actor_id` |
| Raiden | #12 Pattern evidence note + class diagram update |
| Cristian | #13 Listing review and publish notifications (added during the sprint) |
| Jelani | #14 Coverage report |
| Group | #15 Sprint 2 review + retrospective |

## Review (done at the end)

| Owner | Task Number & Title | Status | Comments |
|---|---|---|---|
| Raiden | #1 Sprint 2 planning | Completed | Sprint 2 cards created on the board; #13 was added during the sprint. |
| Raiden | #2 State pattern classes | Completed | `application_states.py`: five states, `IllegalTransition`, `state_for()`. PR #13. |
| Raiden | #3 Unit tests for the states | Completed | Legal and illegal transitions for every state. PR #14. |
| Raiden | #4 Remove the status flags | Completed | Reassigned from Jelani. `Application.status` is the only lifecycle field (D3, D4). PR #15. |
| Raiden | #5 Route transitions through the State pattern | Completed | Reassigned from Jelani. `transition_application()` → `apply_action()` → state. PR #19. |
| Raiden | #6 Test database fixture + integration tests | Completed | Reassigned from Jelani. `lifecycle_db` fixture and full-lifecycle tests. PR #20. |
| Cristian | #7 Listing ownership checks | Completed | Only the listing's employer may transition or view applicants; checked before the state is called (D5, A7). PR #18. |
| Cristian | #8 Error-to-HTTP mapping | Completed | Illegal transition 409, forbidden 403, not found 404, invalid action 400 (D6). PR #17. |
| Cristian | #9 Regression tests for the audit defects | Completed | One test per defect (D1–D7, A2–A7); 14 of 16 fail on pre-fix code. PR #21. Updated for session auth with new A1 tests in PR #25. |
| Cristian | #10 Eligibility and listing rules | Completed | A2–A6 fixed: DCIT-only subscribe/apply, hidden pending/expired listings, no in-app apply to external listings. PR #16. |
| Jelani | #11 Session auth instead of `actor_id` | Completed | Acting user now comes from the JWT cookie (A1). PR #22. Follow-up fixes (submit_listing crash, leftover `actor_id` fields, JSON 401 for `/api`) in PR #25, agreed with Jelani. |
| Jelani / Raiden | #12 Pattern evidence + class diagram | Completed | Reassigned from Raiden. `PatternEvidence.md` and updated diagram source (PR #23); PNG export (PR #26). |
| Cristian | #13 Listing review and publish notifications | Completed | Added after planning to close the last acceptance-criteria gaps: new listings start pending (A8, AC 4); publishing notifies eligible subscribers once (A9/A10, AC 7). `Notification` now stores `listing_id`. |
| Jelani / Cristian | #14 Coverage report | Completed | First report in PR #24 measured two modules before session auth; refreshed to a full-suite run, 58 passed, `pytest-cov` added (PR #27). |
| Group | #15 Sprint 2 review + retrospective | Completed | This report. |

Note: cards #13–#15 were renumbered on the board when the listing-review card was added. The coverage commit in PR #27 is labelled `S2-#13`; it belongs to card #14.

## Retrospective

**What went well**
- The State pattern from the Sprint 1 design was implemented as planned; the transition rules did not change.
- Every audit defect fixed in Sprint 2 has a test named after its ID, and the tests were confirmed to fail on the pre-fix code.
- Error codes (#8) made later work simpler: the ownership check (#7) only had to return `forbidden` to get a 403.
- Work reached `main` through pull requests, as agreed in the Sprint 1 retrospective.

**What didn't go well**
- Merging #11 broke 15 tests on `main` because the tests were not run before merging; it was fixed in PR #25.
- Several cards were done by someone other than the planned owner (#4, #5, #6, #12), so the board had to be updated afterwards.
- Some branch names (`ApplicationStates`, `flags`, `classFix`) and commits do not include the card number, which makes the history harder to trace.
- Many PRs were merged within minutes, with little review.
- Files were renamed by accident during a diagram export (`class-diagram (1).puml`), breaking links until fixed.

**What we'll change in Sprint 3**
- Run `python -m pytest tests -q` on the branch, after pulling `main`, before every merge.
- Name every branch and commit with the card number (`S3-#n`).
- The reviewer is never the author, and reviews before merging.
- Update Trello when a card changes hands, not afterwards.

## Known gaps (carried into Sprint 3 backlog)

- A logged-in non-admin calling an admin route receives 401 instead of 403 (FastStart `is_admin_dep`).
- Rare error branches (unknown stored status, an application whose listing was deleted) are not tested.
