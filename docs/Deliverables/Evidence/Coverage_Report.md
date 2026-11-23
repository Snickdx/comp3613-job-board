# Test Coverage Report (S2-#13)

## Summary

Full test suite run on `main` after PR #25 (session-auth follow-up and updated regression tests).

- **Result:** 58 passed, 0 failed
- **Command:** `python -m pytest tests -q --cov=app --cov-report=term`
- **Evidence:** screenshot in [`13_Coverage/`](13_Coverage/)

`pytest-cov` is now listed in `requirements.txt`, so `pip install -r requirements.txt` is enough to reproduce the run.

## Coverage of the code changed in Sprint 2

| Module | Role in Sprint 2 | Statements | Missed | Coverage |
|---|---|---:|---:|---:|
| `app/services/application_states.py` | State pattern: states, transitions, `IllegalTransition` | 56 | 2 | **96%** |
| `app/services/applications.py` | Apply, ownership checks, `transition_application()` | 82 | 7 | **91%** |
| `app/services/board_auth.py` | User lookup for the job-board services | 25 | 3 | **88%** |
| `app/routers/board.py` | JSON API, session auth, error-to-HTTP mapping | 93 | 12 | **87%** |
| `app/services/lifecycle.py` | Context: `apply_action()` calls the state | 16 | 3 | **81%** |
| `app/services/listings.py` | Eligibility, job visibility, listing workflow | 76 | 32 | **58%** |
| `app/models/*` | `Application`, `Listing`, `User`, etc. | — | 0 | **100%** |

The special feature (the State pattern and the code that drives it) is covered at **81–96%**.

## Whole application

| Scope | Statements | Missed | Coverage |
|---|---:|---:|---:|
| All of `app/` | 2460 | 1706 | **31%** |

The whole-application figure is low because `app/` also contains FastStart starter code that this
project did not change and does not test: the server configuration pages
(`routers/server_config.py`), PDF report and transcript export, the CLI, the use-case diagram
generator and the HTML page routes. These are outside the job-board scenario.

## Known gaps (honest)

- **Listing workflow is not tested** (`listings.py` 58%): `submit_listing()`, `publish_listing()`
  and `notify_subscribers()` have no tests beyond one publish call in `test_A6`. These relate to
  defects A8–A10 (new listings publish immediately; publishing does not notify; notify has no
  eligibility filter or duplicate check), which were **not fixed in Sprint 2** and are carried
  into the backlog.
- **Admin-only routes**: `/admin/listings/pending` and `/admin/listings/{id}/notify` are not
  called by any test.
- **Rare error branches** in `applications.py` and `lifecycle.py` (for example an unknown stored
  status, or an application whose listing was deleted) are not exercised.
- **Non-admin on an admin route** returns 401 instead of 403 (FastStart's `is_admin_dep`); there
  is no test for this case.
- `tests/test_scenario.py` calls `seed(reset=True)` on the configured database. Run the tests
  against a disposable database so working data is not reset.

## Test files

| File | What it covers |
|---|---|
| `tests/test_unit.py` | Password hashing, JWT claims, every legal and illegal state transition |
| `tests/test_integration.py` | Registration/login, full employer-owned lifecycle, reopen, non-owner and admin refused |
| `tests/test_regression.py` | One test per audit defect: D1–D7, A1–A7, plus 400/404 error codes (18 tests) |
| `tests/test_scenario.py` | Smoke tests: health, API login sets the session cookie, job list |
