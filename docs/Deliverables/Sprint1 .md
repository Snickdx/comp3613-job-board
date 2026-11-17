# Sprint 1 — Requirements & Design

**Scenario:** Job board · **Special feature:** Application lifecycle / transitions 

## Team roster

| Name | Student ID | GitHub username |
|---|---|---|
| Cristian Rampersad | `[816044517]` | `cris24TT` |
| Raiden Ramdath | `[816044899]` | `raidenrUWI]` |
| Jelani Franics | `[816044626]` | `Jelanidprogram` |

## Links

| Item | Link |
|---|---|
| Repository | https://github.com/raidenrUWI/comp3613-job-board |
| Starter repo | comp3613-job-board (Job board scenario) |
| Trello board (invite link) | `https://trello.com/invite/b/6af7ad646f2d22abde7fe0fe/ATTIedf5291e397dfc1d0ea4b62bfb133f41FAD2DDF6/3613sprint1` |

## Sprint 1 deliverables (in `docs/Deliverables/`)

Commit hashes link to the commit on GitHub. **Content commits** are where the work was written; the **merge** is the pull request that brought it into `main`. Commits marked *direct* were pushed to `main` without a PR.

| # | Deliverable | Location | Content commits (author) | Merged into `main` via |
|---|---|---|---|---|
| 1 | Roster, scenario/repo URL, Trello invite link | `Sprint1.md` (this file) | `[this commit]` | `[this PR]` |
| 2 | Prioritized requirements with interview traceability | `Requirements/Job Board Requirements & Interview Traceability.md` | [`7c70780`](https://github.com/raidenrUWI/comp3613-job-board/commit/7c70780) initial (Jelani, *direct*); [`8f14086`](https://github.com/raidenrUWI/comp3613-job-board/commit/8f14086) special feature correction (Jelani) — added to the top-level `Requirements/` folder, not yet copied into `docs/Deliverables/` | [`2493dcb`](https://github.com/raidenrUWI/comp3613-job-board/commit/2493dcb) PR #5 (copy into Deliverables, by Raiden); [`7f52ed6`](https://github.com/raidenrUWI/comp3613-job-board/commit/7f52ed6) PR #11 (correction) |
| 3 | Use case diagram + actor notes | `diagrams/UseCaseDiagram/` | [`bbba1af`](https://github.com/raidenrUWI/comp3613-job-board/commit/bbba1af), [`efb413b`](https://github.com/raidenrUWI/comp3613-job-board/commit/efb413b), [`a4510fa`](https://github.com/raidenrUWI/comp3613-job-board/commit/a4510fa), [`71a9a1d`](https://github.com/raidenrUWI/comp3613-job-board/commit/71a9a1d) initial (Raiden, *direct*); [`0e0577c`](https://github.com/raidenrUWI/comp3613-job-board/commit/0e0577c) revision showing the special feature (Raiden) | [`200385a`](https://github.com/raidenrUWI/comp3613-job-board/commit/200385a) PR #4 (revision only; earlier commits were direct) |
| 4 | Class diagram (State pattern vs inherited design) | `diagrams/ClassDiagram/` | [`0a007af`](https://github.com/raidenrUWI/comp3613-job-board/commit/0a007af) first version; [`fcbea4a`](https://github.com/raidenrUWI/comp3613-job-board/commit/fcbea4a) inherited view, state methods, `fromStatus()` (Raiden) | [`30dcb5b`](https://github.com/raidenrUWI/comp3613-job-board/commit/30dcb5b) PR #7; [`aec3cc9`](https://github.com/raidenrUWI/comp3613-job-board/commit/aec3cc9) PR #9 |
| 5 | Pattern rationale | `Requirements/PatternRationale.md` | [`59440c9`](https://github.com/raidenrUWI/comp3613-job-board/commit/59440c9) rationale; [`f5ebc8c`](https://github.com/raidenrUWI/comp3613-job-board/commit/f5ebc8c) links + class diagram mapping (Cristian) | [`bb449dd`](https://github.com/raidenrUWI/comp3613-job-board/commit/bb449dd) PR #6; [`11e9fe0`](https://github.com/raidenrUWI/comp3613-job-board/commit/11e9fe0) PR #8 |
| 6 | Interview transcripts (chosen scenario) | `Interviews/InterviewChat.txt`, `Interviews/Interviews.md`, `Interviews/imgs/` | Screenshots [`cf5a3d0`](https://github.com/raidenrUWI/comp3613-job-board/commit/cf5a3d0), [`7e147d0`](https://github.com/raidenrUWI/comp3613-job-board/commit/7e147d0), [`5038573`](https://github.com/raidenrUWI/comp3613-job-board/commit/5038573) (Raiden, *direct*); text transcript first added as `Interview_Analyze.txt` in [`7c70780`](https://github.com/raidenrUWI/comp3613-job-board/commit/7c70780) (Jelani, *direct*); both moved into Deliverables in [`8febc39`](https://github.com/raidenrUWI/comp3613-job-board/commit/8febc39) | [`2493dcb`](https://github.com/raidenrUWI/comp3613-job-board/commit/2493dcb) PR #5 |
| 6 | Exploratory interviews + scenario selection | `Interviews/Exploratory/` | [`1b20a84`](https://github.com/raidenrUWI/comp3613-job-board/commit/1b20a84) screenshots (Raiden); `ScenarioSelection.md` in `[this commit]` | [`2150458`](https://github.com/raidenrUWI/comp3613-job-board/commit/2150458) PR #10; `[this PR]` |
| 7 | Sprint 1 report | `Sprint1.md` (this file) | [`8febc39`](https://github.com/raidenrUWI/comp3613-job-board/commit/8febc39) planning table (Raiden); `[this commit]` review, retro, roster | [`2493dcb`](https://github.com/raidenrUWI/comp3613-job-board/commit/2493dcb) PR #5; `[this PR]` |
|11 | Lifecycle defect audit (D1–D7) | `Defects/LifecycleAudit.md` | [`70e5fe5`](https://github.com/raidenrUWI/comp3613-job-board/commit/70e5fe5), [`8272af1`](https://github.com/raidenrUWI/comp3613-job-board/commit/8272af1) (Cristian; labelled `#8`, Trello #11) | [`0a54c67`](https://github.com/raidenrUWI/comp3613-job-board/commit/0a54c67) PR #1 |
| 12 | Authorization & listings audit (A1–A11) | `Defects/AuthListingsAudit.md` | [`011bfc1`](https://github.com/raidenrUWI/comp3613-job-board/commit/011bfc1) (Cristian, Trello #12) | [`ede1c57`](https://github.com/raidenrUWI/comp3613-job-board/commit/ede1c57) PR #2 |
| — | Audit formatting and evidence links | both audit files | [`7774452`](https://github.com/raidenrUWI/comp3613-job-board/commit/7774452) (Cristian, Trello #11 #12) | [`0b9f042`](https://github.com/raidenrUWI/comp3613-job-board/commit/0b9f042) PR #3 |
| — | Reorganisation into `docs/Deliverables/` | all of the above | [`8febc39`](https://github.com/raidenrUWI/comp3613-job-board/commit/8febc39) (Raiden) | [`2493dcb`](https://github.com/raidenrUWI/comp3613-job-board/commit/2493dcb) PR #5 |


---

## Planning (done at the beginning)

| Owner | Task Number & Title | Deliverable location |
|---|---|---|
| Group | #1 Scenario decision and roster | `Sprint1.md` |
| Cristian | #2 Trello board setup and invite link | `Sprint1.md` |
| Jelani | #3 Register group and claim job board on swen | — |
| Raiden | #4 Fork repo | Repository |
| Group | #5 Run locally and inspect repo | — |
| Raiden | #6–8 Stakeholder interviews (Graduate, Employer, Admin) | `Interviews/` |
| Group | #9 Interview analysis discussion| — |
| Jelani | #10 Requirements & traceability | `Requirements/` |
| Cristian | #11 Lifecycle defect audit | `Defects/LifecycleAudit.md` |
| Cristian | #12 Authorization & listings defect audit | `Defects/AuthListingsAudit.md` |
| Raiden | #13 Use case diagram | `diagrams/UseCaseDiagram/` |
| Raiden | #14 Class diagram | `diagrams/ClassDiagram/` |
| Cristian | #15 Pattern rationale | `Requirements/PatternRationale.md` |
| Group | #16 Sprint 1 review and retrospective | `Sprint1.md` |

## Review (done at the end)

| Owner | Task Number & Title | Status | Comments |
|---|---|---|---|
| Group | #1 Scenario decision and roster | Completed | Job board chosen: clearest special feature with a demonstrable defect in `lifecycle.py`. |
| Cristian | #2 Trello board setup and invite link | Completed | Five lists and four labels; invite link above. |
| Jelani | #3 Register group and claim job board on swen | Completed | |
| Raiden | #4 Fork repo | Completed | Team fork at `raidenrUWI/comp3613-job-board`; main updated via PRs. |
| Group | #5 Run locally and inspect repo | Completed | Setup issues on Windows (pip launcher, OneDrive auto-reload) resolved. |
| Raiden | #6–8 Stakeholder interviews | Completed | Graduate, Employer and Administrator interviews; text transcript + screenshots. |
| Group | #9 Interview analysis discussion | Completed  | Group had a quick discussion about what was retained from the interviews. |
| Jelani | #10 Requirements & traceability | Completed | MoSCoW-prioritized FR/NFR with interview timestamps. Special feature callout corrected to application lifecycle (FR-05). |
| Cristian | #11 Lifecycle defect audit | Completed | D1–D7 confirmed against the running API with screenshot evidence. |
| Cristian | #12 Authorization & listings defect audit | Completed | A1–A10 defects confirmed; A11 (no password in login response) passes. |
| Raiden | #13 Use case diagram | Completed | Revised to show the lifecycle special feature and missing AC use cases. |
| Raiden | #14 Class diagram | Completed | State pattern participants plus inherited (before) structure. |
| Cristian | #15 Pattern rationale | Completed | State pattern chosen; alternatives, assumptions and Sprint 2 outline documented. |
| Group | #16 Sprint 1 review and retrospective | Completed | |

## Retrospective

**What went well**
- Defect audits gave concrete, reproducible evidence (D1–D7, A1–A10) that directly justified the State pattern.
- Requirements, use case diagram, class diagram and rationale all trace back to the same interview timestamps and acceptance criteria.
- Work was split by Trello card, and most deliverables reached `main` through reviewed pull requests.

**What didn't go well**
- Some early commits were pushed directly to `main` instead of through a PR.
- An early PR targeted the original starter repository instead of our fork, and was closed and re-opened against our fork.
- Several fixes were needed when files were reorganized into `docs/Deliverables/` (broken links, duplicated files).

**What we'll change in Sprint 2**
- Every change goes branch → PR → teammate review → merge; no direct pushes to `main`.
- Check the PR target (`raidenrUWI:main`) before creating it.
- Agree on the folder structure before moving files, and update links in the same PR.
- Start the State-pattern refactor and its tests early.
