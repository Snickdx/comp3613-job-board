# Test Coverage Report

## Summary

The repository contains a historical, targeted coverage result for the application lifecycle and state-pattern modules. It is **not a project-wide coverage measurement**, and it predates the session-authentication changes.

| Module | Statement coverage |
|---|---:|
| `app/services/application_states.py` | 96% |
| `app/services/lifecycle.py` | 81% |
| **Combined for the measured modules** | **93%** |

The recorded run reported **56 tests passed**.

## Scope and test areas

The test suite includes:

- Unit tests for password hashing, token claims, and application-state transitions (`tests/test_unit.py`).
- Integration tests for user registration, authentication, and application lifecycle behavior (`tests/test_integration.py`).
- Regression tests for lifecycle defects, listing eligibility, and authorization rules (`tests/test_regression.py`).
- Scenario smoke tests for health, API login, and job listing responses (`tests/test_scenario.py`).

## Limitations

- The recorded command measured only `application_states.py` and `lifecycle.py`; the 93% figure must not be interpreted as overall application coverage.
- The result was recorded for commit `06903a7`, before session authentication was merged. It does not report coverage for the current code.
- No current full-project coverage run is included here.
- `pytest-cov` is not listed in `requirements.txt`; it may need to be installed to reproduce the coverage command.
- `tests/test_scenario.py` calls `seed(reset=True)`. Run tests against a disposable database to avoid resetting working data.

## Reproducing the historical targeted measurement

```powershell
pytest -q --cov=app.services.application_states --cov=app.services.lifecycle