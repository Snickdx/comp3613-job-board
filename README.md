# COMP 3613 Job Board (Phase 2 starter)

Flawed baseline **0.2.0** built on [uwidcit/faststart](https://github.com/uwidcit/faststart) (`96ccfce`).

FastStart provides the SSR shell, JWT cookie auth, SQLModel, `manage.py`, and Render/Docker wiring. The job-board scenario adds domain models/services and a JSON API under `/api` (see `/docs`).

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py init
python manage.py run
```

## Seeded API accounts

| Email | Password | Role |
| --- | --- | --- |
| `admin@example.com` | `admin-dev` | admin |
| `grad.dcit@example.com` | `grad-dev` | graduate (DCIT) |
| `grad.other@example.com` | `grad-dev` | graduate (OTHER) |
| `employer@example.com` | `employer-dev` | employer |
| `employer2@example.com` | `employer-dev` | employer |

JSON login: `POST /api/auth/login` with `{"email","password"}`.

## Student brief

See [`ASSIGNMENT.md`](ASSIGNMENT.md) and [`docs/ACCEPTANCE.md`](docs/ACCEPTANCE.md).

## Tests

```bash
python -m pytest tests -q
```
