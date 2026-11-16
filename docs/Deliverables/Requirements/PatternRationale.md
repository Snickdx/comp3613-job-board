# Pattern rationale — Application lifecycle (special feature)

Scenario: Job board (`comp3613-job-board`). Trello task: #13.

Evidence used in this document:

| Evidence | Location |
|---|---|
| Lifecycle defect audit (D1–D7) | [Defects/LifecycleAudit.md](Defects/LifecycleAudit.md) |
| Authorization & listings audit (A1–A11) | [Defects/AuthListingsAudit.md](Defects/AuthListingsAudit.md) |
| Interview transcript (timestamps cited below) | [Interviews/InterviewChat.txt](Interviews/InterviewChat.txt) |
| Requirements (FR/NFR IDs cited below) | [Requirements/Job Board Requirements & Interview Traceability.md](<Requirements/Job Board Requirements & Interview Traceability.md>) |
| Public acceptance criteria (AC numbers) | [Requirements/ACCEPTANCE.md](Requirements/ACCEPTANCE.md) |

Interview citations use the same format as the requirements document, e.g. *Item 3 (Employer) @ 07:47 AM*.

## 1. Special feature

The brief assigns the job board scenario the special feature **"Application lifecycle / transitions"**.
Every application moves through `submitted → reviewed → shortlisted → rejected | hired` (AC 10),
only legal transitions are allowed, the applicant sees one consistent status (AC 11), and only the
employer who owns the listing may advance it (AC 12). This is requirement **FR-05**.

Stakeholders confirm both the stages and why they matter:

- The graduate lists the same five statuses: submitted, reviewed, shortlisted, rejected, hired
  (*Item 1 (Graduate) @ 02:42 AM*), and says tracking them is "really important … so I know where
  I stand" (*Item 1 (Graduate) @ 02:41 AM*).
- The employer reviews applications and updates their statuses "for my listings"
  (*Item 3 (Employer) @ 02:48 AM*), moving them to hired or rejected after assessment
  (*Item 3 (Employer) @ 07:47 AM*).

Related stakeholder requests — status-change notifications (FR-08) and direct messaging (FR-09) —
build on the lifecycle but are not the special feature itself.

## 2. Inherited design and its defects

The starter tracks the lifecycle in `app/services/lifecycle.py`:

- Each `Application` row stores a `status` string **and** four parallel flags
  (`flag_reviewed`, `flag_shortlisted`, `flag_rejected`, `flag_hired`).
- One function, `apply_action()`, updates both through a long nested `if/elif` that checks the
  status and the flags in different combinations.
- The graduate view ignores `status` and recomputes a status from the flags
  (`derived_status_from_flags()`).

We confirmed the resulting defects by testing the running API (evidence in `LifecycleAudit.md`):

| Defect | What happens | Root cause in the inherited design |
|---|---|---|
| D1 | `hire` accepted straight from `submitted` | Nothing defines which moves are legal from each status |
| D2 | A rejected application can be shortlisted; ends with `flag_rejected=1` **and** `flag_shortlisted=1` | No legal-transition rules; flags updated independently of status |
| D3 | `reopen` sets status to `submitted` but leaves `flag_hired=1` | Status and flags are two copies of the same fact |
| D4 | The graduate sees `hired` while the stored status is `submitted` | Two sources of truth (column vs flags) |
| D5 | Another employer or the admin can advance someone else's application | Authorization gap — not a lifecycle problem (see §5) |
| D6 | An illegal action on a hired application returns `ok` and silently does nothing | Illegal moves handled inconsistently, branch by branch |
| D7 | Two different response shapes for the same application | Response built separately from the stored row |

**D4 is the clearest user-facing failure.** The graduate's main concern is knowing where they
stand (*Item 1 (Graduate) @ 02:41 AM*), and the inherited design can show them a different status
from the one the employer set.

## 3. Pattern chosen: State

We use the **State pattern**: each lifecycle stage becomes its own class that knows which actions
are legal from that stage and which stage each one leads to.

### Participants

| GoF role | Our class | Responsibility |
|---|---|---|
| State (abstract) | `ApplicationState` | Declares every action: `review`, `shortlist`, `reject`, `hire`, `reopen`. The default implementation raises `IllegalTransition`. |
| Concrete states | `SubmittedState`, `ReviewedState`, `ShortlistedState`, `RejectedState`, `HiredState` | Each overrides **only** the actions legal from that stage and returns the next state. |
| Context | `Application` (model) + `ApplicationLifecycle` | Stores a single `status` value, looks up the matching state object and delegates the action to it. |
| Client | `transition_application()` (service layer) | Checks who is acting, then asks the context to perform the action and saves the result. |

### Transition rules

| From | Legal action → next state | Basis |
|---|---|---|
| Submitted | `review` → Reviewed | AC 10; employer reviews before deciding (*Item 3 (Employer) @ 07:47 AM*) |
| Reviewed | `shortlist` → Shortlisted; `reject` → Rejected | AC 10; graduate's stage order (*Item 1 (Graduate) @ 02:42 AM*) |
| Shortlisted | `hire` → Hired; `reject` → Rejected | AC 10; *Item 3 (Employer) @ 07:47 AM* |
| Rejected | `reopen` → Reviewed | Employer wants rejected applications kept "in case I want to revisit them later" (*Item 3 (Employer) @ 07:47 AM*; FR-10) |
| Hired | *(none — final)* | AC 10; no stakeholder asked to reverse a hire |

Any action not listed raises `IllegalTransition`, which the API returns as an error (400/409)
instead of silently succeeding.

### Why State fits this problem

1. **Illegal transitions become impossible by construction.** `SubmittedState` has no `hire`
   implementation, so D1, D2 and D6 cannot happen. Each rule lives with the stage it belongs to
   instead of in one large conditional.
2. **One source of truth.** The four flags are removed; `status` is the only stored value and every
   view reads it. This removes D3, D4 and D7 at the root and satisfies AC 11.
3. **Behaviour per stage has a natural home.** Stakeholders want things to happen when an
   application *enters* a stage: a notification once it has been reviewed
   (*Item 1 (Graduate) @ 02:46 AM*; FR-08) and next steps for hired applicants
   (*Item 3 (Employer) @ 07:47 AM*). With State, that logic belongs in the relevant state class
   rather than another `if` branch.
4. **Open/Closed and Single Responsibility.** Adding a stage later (e.g. "interview scheduled")
   means adding one class and changing the one state that leads to it — not editing a function
   that handles every case. Each class has one job: the rules for one stage.
5. **Testable.** Each state can be tested in isolation: one test per legal move and one per
   illegal move.

## 4. Alternatives considered

| Alternative | Why not chosen |
|---|---|
| **Keep and patch the nested `if/elif`** | This produced D1–D7. Every fix adds another branch, and the status/flag duplication remains. |
| **Transition table** (a dict of `(status, action) → next status`) | Fixes illegal jumps and is simpler — a close second. We chose State because stakeholders want behaviour attached to stages (FR-08, *Item 3 (Employer) @ 07:47 AM*), which a table cannot hold without growing separate conditionals around it. |
| **Strategy** | Strategy swaps interchangeable algorithms chosen by the client. Here behaviour must change automatically as the application's own stage changes, which is what State is for. |
| **Enum + `match` statement** | Cleaner than flags, but still one central function that must be edited for every new rule (not Open/Closed). |

## 5. What the pattern does not fix

State controls **which moves are legal**. It does not decide **who may make them**. These checks
stay in the service layer and run **before** the state object is called:

- **Listing ownership** (D5, A7): only the employer who owns the listing may advance its
  applications or view its applicants (AC 12, AC 15; NFR-02). The employer describes managing
  statuses "for my listings" (*Item 3 (Employer) @ 02:48 AM*). The administrator does not change
  application status (AC 12); the administrator's own description of their role covers listings and
  notifications only (*Item 2 (Admin) @ 08:08 AM*).
- **Authenticated identity** (A1): the acting user comes from the logged-in session, not from an
  `actor_id` sent in the request.

Keeping authorization out of the state classes keeps each class focused on one concern.

## 6. Sprint 2 change outline

1. **Add the states.** Create `app/services/application_states.py` with `ApplicationState`, the
   five concrete states, `IllegalTransition`, and a lookup from status string to state object.
2. **Simplify the model.** Remove the four `flag_*` columns from `Application`; `status` is the only
   lifecycle field. Update the seed data accordingly.
3. **Rewrite `transition_application()`.** Order: identify the acting user → check they own the
   listing → look up the current state → call the action → save the new `status` → return the full
   application in one consistent shape.
4. **Fix the graduate view.** `my_applications()` returns the stored `status`; delete
   `derived_status_from_flags()` and the old `apply_action()`.
5. **Return clear errors.** Illegal transitions return 400/409 with a message such as
   "cannot hire an application in status submitted".
6. **Tests.**
   - Every legal transition (four forward moves, two rejects, reopen) succeeds and stores the right status.
   - Every illegal transition from every state is refused (e.g. hire from submitted, shortlist from
     rejected, anything from hired).
   - A non-owning employer and the admin are refused (403).
   - The graduate and the employer see the same status after every transition.
   - The D1–D7 scenarios are re-run as regression tests.

## Assumptions and open points

These rules are our interpretation, not direct stakeholder statements:

- **No reject before review.** The employer describes reviewing applications before deciding
  (*Item 3 (Employer) @ 07:47 AM*), so `SubmittedState` does not allow `reject`. If a stakeholder
  says otherwise, this is a one-method change.
- **Reopen goes to Reviewed.** The employer wants to "revisit" rejected applications; we interpret
  that as returning them to Reviewed rather than Submitted. To be confirmed with the Employer.
- **Status-change notifications (FR-08)** are a requested improvement, not an acceptance criterion.
  The design leaves room for them in each state class; they are in Sprint 2 scope only if time allows.
