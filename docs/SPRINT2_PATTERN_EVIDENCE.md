# Sprint 2 Pattern Evidence: Application Lifecycle State Pattern

## 1. Introduction

This note records the implementation evidence for Task #28, the Application
Lifecycle State Pattern. Its intended role is to show why the State Pattern
was selected, how it represents the five application states, and how transitions
and tests provide evidence of its behavior.

The repository is not currently in a fully implemented State Pattern state:

- `app/services/lifecycle.py` still contains the original procedural flag-based
  implementation.
- `app/services/applications.py` still uses `derived_status_from_flags`.
- `docs/SPRINT2_LIFECYCLE_DESIGN.md` is not present in the repository.
- `tests/test_lifecycle.py` is not present in the repository.

A read-only attachment named `file_test_lifecycle.py` was provided and defines
the intended lifecycle tests. It is evidence of test design, not evidence that
those tests exist in or pass from the project workspace.

## 2. Why the State Design Pattern was Selected

The State Pattern is appropriate because the legal lifecycle operations depend
on the application's current status. Separate state objects can own the actions
allowed from each status instead of mixing status checks and Boolean flags in
one conditional block.

The intended five-state design is:

- `SubmittedState`
- `ReviewedState`
- `ShortlistedState`
- `RejectedState`
- `HiredState`

This design separates lifecycle rules from the router and keeps authorization
outside the State Pattern. Employer ownership and administrator permissions
belong in the application service or authorization layer, not in individual
state classes.

## 3. Problem with the Original Lifecycle Implementation

The current `app/services/lifecycle.py` combines `Application.status` with
four Boolean flags:

- `flag_reviewed`
- `flag_shortlisted`
- `flag_rejected`
- `flag_hired`

The original implementation uses nested conditions across those fields. This
creates the following problems:

- Status and flags can disagree.
- Submitted applications can reach Shortlisted or Hired through invalid paths.
- Rejected applications can be shortlisted or reviewed.
- Hired applications can be changed by some actions.
- Reopen resets the status but does not synchronize the flags.
- An action can return a success with no change where another state expects a
  clear invalid-transition result.

`derived_status_from_flags` also defines a second, flag-derived interpretation
of status. `app/services/applications.py` uses this function for graduate
application views, so status can disagree with the status column.

The State Pattern should remove these secondary interpretations and make
`Application.status` the single source of truth.

## 4. The Abstract ApplicationState Class

The implementation has not yet introduced `ApplicationState`. The intended
abstract class must define a canonical `status` property and a
`transition(action)` operation.

Its responsibilities are:

- Declare the interface every lifecycle state implements.
- Expose the state's canonical status name.
- Return the next state object for a legal action.
- Return no transition for an illegal action.

The concrete transition decision belongs in each concrete state rather than in
a central status-and-flag conditional block.

## 5. The Five Concrete State Classes

The five concrete classes are part of the intended implementation. They have
not yet been added to the repository.

### SubmittedState

- Status: `submitted`
- Permitted transition: `mark_reviewed` -> `ReviewedState`
- All other actions: reject

### ReviewedState

- Status: `reviewed`
- Permitted transitions:
  - `shortlist` -> `ShortlistedState`
  - `reject` -> `RejectedState`
- All other actions: reject

### ShortlistedState

- Status: `shortlisted`
- Permitted transitions:
  - `reject` -> `RejectedState`
  - `hire` -> `HiredState`
- All other actions: reject

### RejectedState

- Status: `rejected`
- Proposed explicit transition: `reopen` -> `SubmittedState`
- All other actions: reject

The rejected-to-submitted reopen rule is explicit and exceptional. The group
must confirm and defend this rule before implementation or presentation.

### HiredState

- Status: `hired`
- Permitted transitions: none
- Every action: reject

## 6. Application Lifecycle Transition Table

The documented and intended transition table is:

| Current state | Action | Next state | Result |
|---|---|---|---|
| Submitted | `mark_reviewed` | Reviewed | Legal |
| Submitted | `shortlist` | None | Illegal |
| Submitted | `reject` | None | Illegal |
| Submitted | `hire` | None | Illegal |
| Submitted | `reopen` | None | Illegal |
| Reviewed | `shortlist` | Shortlisted | Legal |
| Reviewed | `reject` | Rejected | Legal |
| Reviewed | `mark_reviewed` | None | Illegal |
| Reviewed | `hire` | None | Illegal |
| Reviewed | `reopen` | None | Illegal |
| Shortlisted | `reject` | Rejected | Legal |
| Shortlisted | `hire` | Hired | Legal |
| Shortlisted | `mark_reviewed` | None | Illegal |
| Shortlisted | `shortlist` | None | Illegal |
| Shortlisted | `reopen` | None | Illegal |
| Rejected | `reopen` | Submitted | Proposed explicit reopen |
| Rejected | `mark_reviewed` | None | Illegal |
| Rejected | `shortlist` | None | Illegal |
| Rejected | `reject` | None | Illegal |
| Rejected | `hire` | None | Illegal |
| Hired | Any action | None | Illegal |

Unknown actions should also be rejected.

## 7. How Legal Transitions are Handled

The intended `state_for(status)` function should map
`Application.status` to the corresponding concrete state. `apply_action(app,
action)` should then:

1. Validate that the action is in `ACTIONS`.
2. Read the current status.
3. Create the concrete state with `state_for(status)`.
4. Delegate the action to `current_state.transition(action)`.
5. Copy the application dictionary only for a legal transition.
6. Update only `status` on the copy.
7. Return `ok: True`, the updated row/snapshot, and `changed: True`.

The application service can then persist `row.status`. It must not synchronize
or update the four legacy flags as part of lifecycle state.

## 8. How Invalid Transitions are Rejected

Invalid transitions must be rejected in two places:

- Unknown action names must fail with an unknown-action error.
- A concrete state must return no next state for an action it does not permit.

The failure result should contain `ok: False` and a clear error. It should not
mutate the original application dictionary, and it should not cause the
application service to save a change.

Hired must never return a successful no-op. Any attempt to change it must
return a clear failure.

## 9. Why Hired is a Terminal State

Hired is terminal because no reviewed, rejected, reopened, shortlisted, or
other lifecycle path from Hired should exist. `HiredState.transition` must
always reject its action and return no next state.

## 10. Application.status as the Single Source of Truth

After the State Pattern is implemented, `Application.status` must determine:

- Which concrete state object is selected.
- Which actions are legal.
- The status stored after a successful transition.

The four Boolean fields must not determine the current state or decide
transition legality. The legacy fields may remain in the current model for
database compatibility, but they must not be synchronized or used as a second
source of lifecycle truth.

The current `derived_status_from_flags` helper and related flag-derived service
logic must be removed or left unused in the final implementation.

## 11. Testing and Verification

The read-only attached test design in `file_test_lifecycle.py` covers:

- All six legal transitions.
- Illegal transitions from every state.
- Unknown action names.
- Concrete state selection with `state_for`.
- Hired terminal behavior.
- Original-dictionary immutability.
- Legacy flags not changing status.

This test file is attached as evidence, but it is not present in the workspace
and does not currently run in the project test suite.

The actual available project tests were run with:

```text
python -m pytest tests -q
```

Actual result:

```text
10 passed; 0 failed
```

This baseline result verifies the existing project tests. It does not verify
the State Pattern because the lifecycle implementation and lifecycle test module
are not currently present in the workspace.

## 12. Evidence of Implementation

### GitHub Task #18 Pull Request URL

- `[TO BE ADDED]`

### Commit hash

- `[TO BE ADDED]`

### Actual test results

- Existing project suite: `10 passed; 0 failed`
- State Pattern lifecycle suite: not yet runnable because
  `tests/test_lifecycle.py` is absent from the workspace

### Screenshots or other evidence

- Screenshots: No screenshots were provided.
- Source evidence:
  - [Lifecycle implementation](/c:/Users/dines/Downloads/New%20folder/Dev-Dynamics_Comp3613_job_board/app/services/lifecycle.py)
  - [Application service](/c:/Users/dines/Downloads/New%20folder/Dev-Dynamics_Comp3613_job_board/app/services/applications.py)
  - Read-only attached test design:
    `file_test_lifecycle.py`

### Implementation status

The repository currently does not contain the documented State Pattern
implementation or the workspace lifecycle test file. Therefore, this note
records intended evidence requirements and the actual baseline test result
without claiming that implementation work or lifecycle tests have passed.
