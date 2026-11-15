# Job Board — public acceptance criteria

Derived from elicitable stakeholder needs (Phase 1). Use these to drive tests and demos. Instructor private defects and hidden regression tests are **not** listed here.

## Roles

1. Graduates can browse published jobs, subscribe for notifications, and apply.
2. Employers can submit listings and review applicants for **their** listings.
3. Administrators review/publish listings, notify subscribers, and can export applicant packages.

## Listings

4. Employer-submitted listings are **not** visible to graduates until an administrator publishes them.
5. Each listing declares apply mode: **external-link** or **on-platform collect**.
6. After a listing deadline passes, the listing is hidden from graduates.
7. Publishing a listing notifies subscribers without a separate manual step (or an equivalent automatic path).

## Applications & lifecycle

8. Only eligible programme graduates (currently DCIT) may subscribe or apply.
9. On-platform apply captures cover letter + resume and starts at status `submitted`.
10. Application lifecycle is `submitted → reviewed → shortlisted → rejected|hired` with **only legal transitions** (no jumps, no terminal→active without an explicit reopen rule you can defend).
11. Applicants see one consistent current status (not conflicting labels/flags).
12. Only the **listing employer** may advance application lifecycle (not administrators; not other employers).
13. External-link listings send applicants off-platform; the board must not pretend those applications were collected in-app.

## Trust / data

14. Passwords are stored hashed; login responses never include password material.
15. Employers must not access applicant data for listings they do not own.
16. Admin export of applicant packages is allowed for forwarding; treat applicant data carefully.
