
# Pattern Rationale

## 1. Special Feature

The special feature of the Job Board system is **Application Lifecycle / Transitions**, which manages job applications through five statuses:

- Submitted
- Reviewed
- Shortlisted
- Rejected
- Hired

### 1.1 Facts and Assumptions

#### Facts (Consistent Across the Interviews)

- Applications must follow defined transitions, cannot skip stages (Q28, Q30), and cannot move backward (closing clarification).
- Hired and Rejected are final states (Q8, Q24, Q25).
- Rejected applications cannot be reopened (Q9).
- Invalid transitions must be prevented with an error or a refusal (Q11).
- Only the employer who owns the listing may change an application's status (Q7, Q29).

#### Contradictions in the Stakeholder's Answers

**Who rejects:**
- Q19 and Q23 say only the administrator can reject.
- Q7, Q24, Q25, Q29, and the closing clarification say only the employer can.

**Where rejection is reachable:**
- Q25 allows Submitted → Rejected.
- Q29 and the closing summary allow rejection only from Reviewed or Shortlisted.

#### Assumption

We follow the later, more detailed answers (Q29 and the closing summary).

Only the owning employer changes statuses, administrators never do, and Rejected is reachable only from Reviewed and Shortlisted.

This assumption determines the transitions defined in each state class.

### 1.2 Transition Table

| Current State | Allowed Next States |
|---------------|---------------------|
| Submitted | Reviewed |
| Reviewed | Shortlisted, Rejected |
| Shortlisted | Hired, Rejected |
| Rejected | None (final) |
| Hired | None (final) |

---

## 2. Target Defects

The inherited `app/services/lifecycle.py` contains the following defects:

| Defect | Effect | How the Pattern Fixes It |
|--------|--------|--------------------------|
| `apply_action()` allows Submitted → Shortlisted or Hired | Required stages are bypassed (Q28–Q30) | Each state class exposes only its own valid transitions, preventing skipped stages. |
| A status string is stored alongside four boolean flags (`flag_reviewed`, `flag_shortlisted`, `flag_rejected`, `flag_hired`) | Records become inconsistent after status changes | The flags are removed through a migration, and status becomes the single source of truth. |
| Rejected applications can be shortlisted or hired, and hired applications can be rejected | Final states are not final (Q8, Q24) | `RejectedState` and `HiredState` reject every action with an `InvalidTransitionError`. |
| The `reopen` action resets the status to Submitted without clearing flags | Contradicts Q9 and corrupts data | The `reopen` action is removed because the requirements do not allow it. |
| Some invalid actions return a success response without changing anything | Failures are silent (Q11) | Invalid transitions raise `InvalidTransitionError`, which the routes map to HTTP 409. |

---

## 3. Identified Pattern and Why

The **State Design Pattern** was selected because an application's behavior depends on its current status.

The inherited code uses nested conditionals and multiple flags to decide how an application changes status.

We replace this with an `ApplicationState` interface and five concrete classes:

1. `SubmittedState`
2. `ReviewedState`
3. `ShortlistedState`
4. `RejectedState`
5. `HiredState`

Each class defines its own permitted transitions, and the two final states permit none.

### 3.1 SOLID Justification

- **Single Responsibility Principle (SRP):** Transition logic for each status lives in its own class, and authorization stays outside the state classes.
- **Open/Closed Principle (OCP):** The lifecycle can be extended by adding or changing a state class instead of editing a large conditional.
- **Dependency Inversion Principle (DIP):** An `ApplicationStateFactory` maps stored status strings to state objects, so the service layer depends on the `ApplicationState` abstraction rather than concrete states.

### 3.2 Alternative Considered: Table-Driven Transition Map

A table-driven transition map is simpler, and for the five transitions alone it would be sufficient.

We rejected it because the stakeholder raised several likely state-specific behaviors that a static table cannot hold cleanly:

- Recording a history of status changes with who and when (Q10).
- Notifying applicants of status changes (Q12 and the closing note).
- Recording a rejection reason (Q31).

With the State Pattern, these behaviors can attach to the relevant state class without changing the service layer.

This mitigates the **YAGNI/KISS** concern because the requirements point to these extensions rather than relying entirely on speculation.

A state-transition diagram will accompany the class diagram so the rules are visible at a glance.

---

## 4. High-Level Change Outline for Sprint 2

1. **Write tests first:** Create unit tests that reproduce the existing invalid transitions, final-state violations, and inconsistent flag behavior.

2. **Introduce state classes:** Create the `ApplicationState` interface and five concrete state classes.

3. **Implement a state factory:** Create `ApplicationStateFactory` to map stored status strings to the corresponding state objects.

4. **Introduce consistent error handling:** Define `InvalidTransitionError` and map it to HTTP 409 in the routes.

5. **Refactor lifecycle logic:** Update `apply_action()` in the service layer to:
   - Verify that the acting user is the employer who owns the listing.
   - Delegate the transition to the current state object.

6. **Remove redundant flags:** Remove the four boolean flags from the model and add a migration. Status becomes the single source of truth.

7. **Remove unsupported actions:** Delete the `reopen` action.

8. **Preserve the existing architecture:** Maintain the FastStart layering:

   `Routes → Services → Repositories → Models`

   Keep application lifecycle logic within the service layer.

9. **Run comprehensive tests:** Execute unit and integration tests covering:
   - Valid transitions
   - Invalid and skipped transitions
   - Final-state restrictions
   - Employer authorization
   - HTTP error responses
   - Data consistency
