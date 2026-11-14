# Authorization & listings defect audit (Task #12)

Scenario: Job board. Tested locally via /docs using seeded data.

- Users: 1 admin, 2 DCIT graduate, 3 non-DCIT graduate (OTHER),
  4 employer, 5 employer2
- Listings: 1 = employer 4, published, on-platform collect;
  2 = employer 4, pending, external link;
  3 = employer2, published, expired (deadline 2020-01-01)

Evidence screenshots: `docs/evidence/12-auth-listings-auditPngs/`

| ID | Defect | Location | AC broken | Evidence |
|----|--------|----------|-----------|----------|
1) | A1 | No real authentication: login returns user data but no token/session; every endpoint trusts the `actor_id` sent in the request, so anyone can act as any user | `app/routers/board.py` (all endpoints) | AC 12, AC 15 | [a1](evidence/12-auth-listings-auditPngs/a1.png), [login](evidence/12-auth-listings-auditPngs/a1-login.png) 


2) | A2 | Non-DCIT graduate (id 3) can subscribe to notifications; `ELIGIBLE_PROGRAMMES = {"DCIT"}` is defined but never checked | `app/services/listings.py` `subscribe()` | AC 8 | [a2](evidence/12-auth-listings-auditPngs/a2.png) |

3) | A3 | Non-DCIT graduate (id 3) can apply to a listing — no programme eligibility check on apply | `app/services/applications.py` `apply()` | AC 8 | [a3](evidence/12-auth-listings-auditPngs/a3.png) 

4) | A4 | Graduate job list returns pending (listing 2) and expired (listing 3, deadline 2020) listings — no filter on status or deadline | `app/services/listings.py` `list_jobs_for_graduates()` | AC 4, AC 6 | [a4](evidence/12-auth-listings-auditPngs/a4.png) |

5) | A5 | Graduate can apply to an expired listing (listing 3, deadline 2020-01-01) — no deadline or status check on apply | `app/services/applications.py` `apply()` | AC 6 | [a5](evidence/12-auth-listings-auditPngs/a5.png) |

6) | A6 | Graduate can apply in-app to listing 2, which is still pending and is an external-link listing — board creates an application row it should never collect | `app/services/applications.py` `apply()` | AC 4, AC 13 | [a6](evidence/12-auth-listings-auditPngs/a6.png) |

7) | A7 | IDOR: employer 4 can view applicants (cover letter + resume) for listing 3, owned by employer2 — role checked but listing ownership is not | `app/services/applications.py` `listing_applicants()` | AC 15 | [a7](evidence/12-auth-listings-auditPngs/a7.png) 

8) | A8 | Employer-submitted listing is published immediately (status `published`), skipping the admin review queue — it never appears in pending | `app/services/listings.py` `submit_listing()` | AC 4 | [a8](evidence/12-auth-listings-auditPngs/a8.png), [pending](evidence/12-auth-listings-auditPngs/a8-pending.png) |

9) | A9 | Publishing a listing does not notify subscribers (`notified: false`); notification requires a separate manual endpoint | `app/services/listings.py` `publish_listing()` | AC 7 | [a9](evidence/12-auth-listings-auditPngs/a9.png) |

10) | A10 | Notify sends to all subscribers including ineligible graduate 3 (count = 2), and repeated calls send duplicate notifications for the same listing | `app/services/listings.py` `notify_subscribers()` | AC 7, AC 8 | [a10](evidence/12-auth-listings-auditPngs/a10.png), [repeat](evidence/12-auth-listings-auditPngs/a10-repeat.png) |


## Working as expected

- A11: Login response omits the password; seeded passwords are stored hashed (AC 14).

## Root cause

1. **No real identity.** Every endpoint takes `actor_id` from the request,
   and login issues no token or session, so the server cannot know who is
   actually calling (A1). Every other check below can be bypassed by sending
   a different id.

2. **Authorization checks role, never ownership or eligibility.** Services ask
   "is this user an employer/graduate?" but not "does this employer own the
   listing?" (A7) or "is this graduate in an eligible programme?" (A2, A3, A10).
   `ELIGIBLE_PROGRAMMES` exists but is never used.

3. **Listing rules are not enforced.** Listing `status` and `deadline` are
   stored but ignored when listing jobs (A4) and when applying (A5, A6).
   New listings bypass the pending state entirely (A8), and `apply_mode`
   is not respected (A6).

4. **Publish and notify are disconnected.** Publishing does not trigger
   notifications (A9), and notify has no eligibility filter or duplicate
   protection (A10).

## Implication for Sprint 2

- Derive the acting user from an authenticated session/JWT (FastStart
  already provides JWT cookie auth) instead of a request-body `actor_id`.
- Add explicit ownership checks (listing employer) and eligibility checks
  (DCIT) in the service layer before any action.
- Filter graduate-visible listings to `published` and not past deadline;
  reject applications to pending, expired, or external-link listings.
- New listings start as `pending`; publishing triggers subscriber
  notification once, to eligible subscribers only.
- These are MVP fixes alongside the special-feature (State pattern) refactor
  documented in `docs/defects.md`.