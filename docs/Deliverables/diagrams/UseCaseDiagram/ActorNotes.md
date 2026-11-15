# Use case diagram — actor and use case notes

Source: `use-case.puml` (render with PlantUML) → `UseCase.png`.
AC numbers refer to `docs/ACCEPTANCE.md`. Interview evidence: `docs/evidence/Interviews.md`.

## Actors

| Actor | Description |
|---|---|
| **Graduate** | A programme graduate looking for jobs. Only **DCIT** graduates may subscribe or apply (AC 1, 8). |
| **Employer** | Posts listings and processes applicants for **their own** listings only (AC 2, 12, 15). |
| **Administrator** | Reviews and publishes listings, and exports applicant packages. Does **not** change application status (AC 3, 12). |

All use cases require the actor to be logged in; identity must come from the authenticated session, not from a value sent in the request (see audit A1).

## Use cases

### Graduate
| Use case | Notes | AC |
|---|---|---|
| Browse published jobs | Only `published` listings whose deadline has not passed are shown. | 4, 6 |
| Subscribe to job alerts | «include» Check programme eligibility. | 1, 8 |
| Receive job notifications | Triggered when an admin publishes a listing. | 7 |
| Apply to job | On-platform listings only; captures cover letter + resume; starts at `submitted`. «include» Check programme eligibility. | 8, 9 |
| Go to external apply link | «extend» Apply to job when `apply_mode = external`; the board must not create an in-app application. | 5, 13 |
| View my application status | Shows the single stored status — never a value derived from other fields. | 11 |
| Manage profile & resume | Resume is reused when applying. | 9 |

### Employer
| Use case | Notes | AC |
|---|---|---|
| Submit job listing | New listings start as `pending` until an admin publishes them (Employer interview: listings go to an admin for review before going live). | 2, 4, 5 |
| View applicants for own listing | «include» Verify listing ownership. | 2, 15 |
| **Advance application lifecycle** ★ | **Special feature.** Specialised by Mark reviewed, Shortlist, Reject, Hire. Allowed path: `submitted → reviewed → shortlisted → rejected \| hired`; illegal transitions are refused. «include» Verify listing ownership. Reopen rule to be confirmed with stakeholders. | 10, 11, 12 |
| Send / receive messages | Requested in the Employer interview; **future / low priority**, not in the acceptance criteria. | — |

### Administrator
| Use case | Notes | AC |
|---|---|---|
| Review pending listings | Lists listings awaiting approval. | 3, 4 |
| Publish listing | «include» Notify eligible subscribers — notification happens automatically on publish, once, to eligible subscribers only. | 3, 7 |
| Export applicant package | For forwarding applicants; handle applicant data carefully. | 3, 16 |

### Included behaviour
| Use case | Included by | Purpose |
|---|---|---|
| Check programme eligibility | Subscribe, Apply | Rejects non-DCIT graduates (AC 8). |
| Verify listing ownership | View applicants, Advance lifecycle | Only the listing's employer may proceed (AC 12, 15). |
| Notify eligible subscribers | Publish listing | Automatic notification on publish (AC 7). |

## Changes from the previous version
- Added the special feature explicitly (Advance application lifecycle + its four transitions), replacing "Accept or decline job applications".
- Added missing AC use cases: Browse published jobs, View applicants for own listing, Publish listing, Export applicant package.
- Added «include»/«extend» relationships for eligibility, ownership, notification and external apply links.
- Merged "Select job preferences" into "Manage profile & resume"; marked messaging as future/low priority.
- Replaced individual "Log in" links with a note (all use cases require login).
