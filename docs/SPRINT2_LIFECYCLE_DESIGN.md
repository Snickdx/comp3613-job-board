# Application Lifecycle State Design

## Purpose

The application lifecycle is implemented conceptually with the State design
pattern. The intent is to replace the current status string plus independent
boolean flags and nested conditional logic with one explicit state class for
each application status.

The lifecycle uses exactly these five states:

- Submitted
- Reviewed
- Shortlisted
- Rejected
- Hired

Status names are stored in lowercase as `submitted`, `reviewed`,
`shortlisted`, `rejected`, and `hired` to match the existing application
model and acceptance criteria.

## Abstract State

`ApplicationState` is the abstract base class for the lifecycle. It owns the
behavior common to all states and declares the lifecycle interface.

Its responsibilities are:

- Expose the state's canonical status name.
- Provide `transition(action)`, or the equivalent state-handler operation, for
  actions attempted while an application is in that state.
- Return a new concrete state only for a legal transition.
- Reject unsupported actions or transitions.
- Persist only the canonical next status after a legal transition.

The concrete state classes implement only the transitions that are legal from
their own status. The application or lifecycle context selects the concrete
state from the persisted status and delegates the requested action to that
state.

## Concrete States

### Submitted

The Submitted state represents an in-platform application that has just been
created.

- `mark_reviewed` transitions to Reviewed.
- No other action is legal.

### Reviewed

The Reviewed state represents an application that an employer has reviewed.

- `shortlist` transitions to Shortlisted.
- `reject` transitions to Rejected.
- No other action is legal.

### Shortlisted

The Shortlisted state represents an application selected for further
consideration.

- `reject` transitions to Rejected.
- `hire` transitions to Hired.
- No other action is legal.

### Rejected

The Rejected state is terminal for normal lifecycle processing.

- `reopen` explicitly transitions back to Submitted.
- No other action is legal.

This reopen behavior is an explicit exception to terminal-state behavior. It
must remain visible to the group and be confirmed by stakeholders before it is
made available in the production workflow.

### Hired

The Hired state is terminal.

- No transition is legal from Hired.
- An attempted `reopen` or any other action is rejected.

## Transition Table

| Current state | Action | Result | Legal? |
|---|---|---|---|
| Submitted | `mark_reviewed` | Reviewed | Yes |
| Submitted | `shortlist` | No transition | No |
| Submitted | `reject` | No transition | No |
| Submitted | `hire` | No transition | No |
| Submitted | `reopen` | No transition | No |
| Reviewed | `shortlist` | Shortlisted | Yes |
| Reviewed | `reject` | Rejected | Yes |
| Reviewed | `mark_reviewed` | No transition | No |
| Reviewed | `hire` | No transition | No |
| Reviewed | `reopen` | No transition | No |
| Shortlisted | `reject` | Rejected | Yes |
| Shortlisted | `hire` | Hired | Yes |
| Shortlisted | `mark_reviewed` | No transition | No |
| Shortlisted | `shortlist` | No transition | No |
| Shortlisted | `reopen` | No transition | No |
| Rejected | `reopen` | Submitted | Yes |
| Rejected | `mark_reviewed` | No transition | No |
| Rejected | `shortlist` | No transition | No |
| Rejected | `reject` | No transition | No |
| Rejected | `hire` | No transition | No |
| Hired | Any action | No transition | No |

Unknown actions are rejected in every state.

## How the Pattern Works Together

The lifecycle context is an application status loaded from
`Application.status`. The context:

1. Maps the persisted status to the corresponding concrete state object.
2. Delegates the requested action to that state.
3. Receives the next state for a legal transition or an error for an illegal
   transition.
4. Persists the canonical next status.

For example:

```text
Application.status = "submitted"
ApplicationState factory -> Submitted
Submitted.transition("mark_reviewed") -> Reviewed
Application.status becomes "reviewed"
```

The concrete state objects contain the allowed transition rules. The context
does not need a nested chain of status and flag conditions. This prevents
skipped transitions, terminal-to-active transitions, and conflicting flag
values.

## Persistence and Consistency

`Application.status` is the single source of truth for the lifecycle. The
current status determines which concrete `ApplicationState` object handles a
requested action and, therefore, which transitions are legal.

The four Boolean flags `flag_reviewed`, `flag_shortlisted`, `flag_rejected`,
and `flag_hired` are legacy fields and are not required by the State Pattern
design. The application model and application service logic will not use these
flags to determine the current lifecycle state or to validate transitions.

After a successful transition, only `Application.status` is updated to the
new canonical status. The persisted status is then used to select the next
state object. This avoids conflicting status and flag values and ensures that
there is one consistent lifecycle representation.

## Authorization Boundary

The State pattern defines which lifecycle transitions are legal. It does not
replace the authorization rules enforced by the application service.

Only the employer that owns the listing associated with an application may
attempt a lifecycle action. Administrators and other employers must not be
allowed to advance an application. Authorization must be checked before state
delegation is performed.

## Explicit Reopen Rule

`rejected + reopen = submitted` is a **proposed rule** that the group should
confirm and defend before implementation.

The reopen action:

- Is legal only from Rejected.
- Is not legal from Submitted, Reviewed, Shortlisted, or Hired.
- Returns the application to Submitted.
- Requires the same listing-owner authorization as every other employer action.

This rule differs from an unrestricted terminal-state escape hatch. It permits
one defended exception so a rejected application can be reconsidered from the
beginning. The product group should confirm this behavior before it is
implemented or demonstrated.
