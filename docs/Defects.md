# Lifecycle defect audit (Task #8)

Scenario: Job board. Special feature: application lifecycle tracking.
Tested locally via /docs using seeded users (1 admin, 2 DCIT graduate,
4 employer owning listing 1, 5 employer2).

1) | D1 | Hire allowed directly from `submitted` (skips review and shortlist) | `app/services/lifecycle.py`, `apply_action()` hire branch | AC 10 | evidence/d1.png 

2)| D2 | Rejected application can be shortlisted without reopen; ends with flag_rejected=1 and flag_shortlisted=1 (contradictory), flag_reviewed=0 | `app/services/lifecycle.py`, `apply_action()` shortlist branch | AC 10, AC 11 | evidence/d2.png,D2.0.png

3)| D3 | `reopen` from hired resets status to `submitted` but leaves flag_hired=1; reopen has no defined rule (allowed from any state) | `app/services/lifecycle.py`, `apply_action()` reopen branch | AC 10, AC 11 | evidence/d3.png 

4)| D4 | Graduate view shows a status derived from flags, not the stored status — app 1 shows `hired` (actual `submitted`), app 2 shows `rejected` (actual `shortlisted`) | `app/services/applications.py` `my_applications()`; `app/services/lifecycle.py` `derived_status_from_flags()` | AC 11 | evidence/d4.png 

5)| D5 | Non-owning employer (id 5) and admin (id 1) can advance an application on listing 1 — no ownership check | `app/services/applications.py` `transition_application()` | AC 12 | evidence/d5a.png, d5b.png |

6)| D6 | Illegal action on a hired application (`mark_reviewed`) returns ok/200 with changed=false instead of an error; other illegal actions (shortlist) do return errors — inconsistent handling | `app/services/lifecycle.py`, `apply_action()` mark_reviewed branch | AC 10 | evidence/d6.png 

7)| D7 | Inconsistent response shape: unchanged transitions return a reduced snapshot with boolean flags; changed transitions return the full row with 0/1 integer flags | `lifecycle.py` `snapshot()` vs `applications.py` `transition_application()` | AC 11 (consistency) | evidence/d6.png 

## Root cause
## Root cause

All seven defects trace back to how the application lifecycle is stored
and updated:

1. **Status is stored twice.** Each application has a `status` string *and*
   four boolean flags (`flag_reviewed`, `flag_shortlisted`, `flag_rejected`,
   `flag_hired`). They are updated separately, so they drift out of sync
   (D2, D3).

2. **No defined legal transitions.** All actions go through one large nested
   if/elif in `apply_action()`. Nothing states which moves are allowed from
   each status, so illegal jumps are accepted (D1, D2) and some illegal
   actions are silently ignored instead of rejected (D6).

3. **Two different "sources of truth".** The employer path reads `status`,
   but the graduate view reads the flags (`derived_status_from_flags`), so
   the same application shows different statuses to different users (D4).
   Responses are also built in two different ways (D7).

4. **Authorization is separate from the lifecycle problem.**
   `transition_application()` checks the actor's role but not whether they
   own the listing, so other employers and admins can change status (D5).

## Implication for Sprint 2

- Replace status + flags with a single `status` field.
- Use the **State pattern**: one class per lifecycle stage (Submitted,
  Reviewed, Shortlisted, Rejected, Hired), each defining only its legal
  transitions and raising an error for anything else.
- Every view reads the same status, so users always see one consistent value.
- Keep the ownership check in the service layer, before delegating to the
  state object.