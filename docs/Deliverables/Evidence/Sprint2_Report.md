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

The pattern implementation and its mapping to the Sprint 1 design are documented in [`PatternEvidence.md`](./PatternEvidence.md). The design rationale is in [`PatternRationale.md`](../../Requirements/PatternRationale.md).

## Testing — 15%

Tests exercise the lifecycle at multiple levels:

- **Unit tests:** [`test_unit.py`](../../../tests/test_unit.py) covers legal and illegal transitions, unknown actions, lifecycle action handling, and the application model’s status field.
- **Integration tests:** [`test_integration.py`](../../../tests/test_integration.py) covers a full employer-owned lifecycle, reopening a rejected application, invalid transitions, and attempts by non-owners or administrators.
- **Regression tests:** [`test_regression.py`](../../../tests/test_regression.py) covers lifecycle defects D1–D7 and job-board authorization and eligibility defects.
- **Scenario tests:** [`test_scenario.py`](../../../tests/test_scenario.py) provides smoke tests for application health, API login, and job-list retrieval.

A historical test and coverage run is recorded in [`PatternEvidence.md`](./PatternEvidence.md):

| Recorded result | Value |
|---|---:|
| Tests passed | 56 |
| `application_states.py` coverage | 96% |
| `lifecycle.py` coverage | 81% |
| Combined coverage for those two modules | 93% |

This run was recorded on commit `06903a7`, before session authentication was merged. It measured only the two lifecycle modules, so the 93% result is **not full-project coverage**. It should not be presented as a current test run.

## Evidence and Follow-up

- Regression-test screenshot: [`9-SC1.png`](./9_Regression_Tests/9-SC1.png)
- State-pattern implementation details and defect-to-test mapping: [`PatternEvidence.md`](./PatternEvidence.md)
- Sprint 1 class diagram source: [`class-diagram.puml`](../../diagrams/ClassDiagram/class-diagram.puml)

The existing pattern evidence notes that the class diagram should be updated to match the implemented names and structure. A fresh full-suite test and coverage run should also be recorded against the current commit before reporting current project-wide coverage.