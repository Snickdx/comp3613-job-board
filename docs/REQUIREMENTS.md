# Job Board Requirements

## Functional Requirements

### User Management and Access

1. The system shall support three types of users: graduates, employers, and administrators.
2. The system shall require users to log in, and unauthenticated users shall not be able to see anything on the platform.
3. The system shall allow only eligible programme students to register, subscribe to job alerts, and apply for listings.
4. The system shall allow administrators to suspend or deactivate user accounts.

### Graduates

5. The system shall allow graduates to create and maintain a profile that includes a resume or CV.
6. The system shall allow graduates to subscribe to job alerts.
7. The system shall allow graduates to browse and apply to published job listings.
8. The system shall require a complete profile and a cover letter before an application can be submitted.
9. The system shall allow graduates to view the current status of their own applications.
10. The system shall not allow graduates to edit or withdraw an application after it has been submitted.
11. The system shall hide closed or deleted listings, and their related applications, from graduates.

### Employers

12. The system shall allow employers to create job listings with a title, description, requirements, qualifications, and an application deadline.
13. The system shall allow employers to see the applicants for their own listings.
14. The system shall allow employers to edit a published listing, and the edited listing shall return to Pending until an administrator re-reviews it.
15. The system shall allow employers to close or delete their listings, while keeping the existing applications in the system and visible to the employer.
16. The system shall allow employers to revise and resubmit a rejected listing.

### Listing Review and Publication

17. The system shall place newly submitted listings in a Pending state and keep them hidden until an administrator approves them.
18. The system shall allow administrators to approve or reject listings, and only listings from known companies that are relevant to students shall be published.
19. The system shall hide rejected listings from graduates and inform the employer so the listing can be revised.
20. The system shall automatically notify eligible graduates when a listing is published.
21. The system shall allow administrators to export or forward applicant packages to employers.

### Application Status Lifecycle

22. The system shall give every application exactly one status: Submitted, Reviewed, Shortlisted, Rejected, or Hired, and new applications shall start as Submitted.
23. The system shall allow an application to move from Submitted to Reviewed, from Reviewed to Shortlisted or Rejected, and from Shortlisted to Hired or Rejected.
24. The system shall not allow applications to skip stages, such as moving directly from Submitted to Shortlisted or Hired.
25. The system shall not allow applications to move backward to an earlier status.
26. The system shall treat Hired and Rejected as final statuses and shall not allow any further changes once an application reaches them.
27. The system shall not allow a rejected application to be reopened, so a new application is required to reconsider the candidate.
28. The system shall allow only the employer who owns the listing to change an application's status.
29. The system shall not allow administrators to change application statuses (assumption, because the stakeholder gave conflicting answers about who can reject).
30. The system shall refuse invalid status transitions with an error and leave the application unchanged.

### Desired / Possible Future Features

31. The system should keep a history of application status changes, recording who made each change and when (desired but not confirmed).
32. The system should record the reason an application was rejected (not currently done, but described as potentially helpful).
33. The system should notify graduates when their application status changes (the stakeholder's answers conflict, so this is a possible future feature).

## Non-Functional Requirements

### Security and Privacy

1. The system shall encrypt personal data and store it securely.
2. The system shall enforce strong access controls so that only authorized users can view or manage sensitive information.
3. The system shall undergo regular security audits and monitoring to catch issues early.
4. The system shall keep graduate and employer data private, so graduates can see only their own applications.

### Availability and Reliability

5. The system shall be available at least 99% of the time.
6. The system shall handle failures gracefully by showing friendly error messages and giving users a way to report issues.
7. The system shall minimize downtime and allow problems to be resolved quickly.

### Scalability

8. The system shall support a good volume of users, listings, and applications, with room to grow as demand increases (the stakeholder gave no specific numbers).

### Data Integrity

9. The system shall keep application statuses consistent and valid at all times, using a single source of truth for status (team-derived).

### Usability and Extensibility

10. The system shall make the application process clear and logical for employers and graduates.
11. The system shall allow the application lifecycle to be extended, for example with history, notifications, or rejection reasons, without large rewrites (team-derived).
