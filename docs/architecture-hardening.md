# Architecture Hardening Notes

## Repository Cleanup

Generated artifacts are ignored:

- `.next`
- `node_modules`
- Python caches
- pytest caches
- local databases
- environment files
- TypeScript build info
- one-off scaffold and scratch scripts

The frontend source has been restored under `frontend/src`.

## Secure Auth

Refresh tokens are stored in an `HttpOnly` cookie. The frontend receives access tokens in JSON and uses the refresh endpoint to rotate access when needed.

Cookie-backed refresh and logout require an `X-CSRFToken` header matching the readable auth CSRF cookie.

## Organizations

Organizations represent universities, companies, bootcamps, NGOs, government institutions, and enterprise customers. A user may have different roles in different organizations through `OrganizationMembership`.

Supported organization types are `university`, `company`, `bootcamp`, `ngo`, `government`, `enterprise`, `platform_partner`, and `other`.

Supported scoped membership roles are `student`, `instructor`, `mentor`, `recruiter`, `company_admin`, `university_admin`, `content_moderator`, `finance_admin`, `platform_admin`, and `super_admin`.

Organization APIs live under `/api/v1/organizations/`:

- `GET /api/v1/organizations/`
- `POST /api/v1/organizations/`
- `GET /api/v1/organizations/{id}/`
- `GET /api/v1/organizations/{id}/members/`
- `POST /api/v1/organizations/{id}/invitations/`
- `PATCH /api/v1/organizations/{id}/members/{membership_id}/role/`
- `DELETE /api/v1/organizations/{id}/members/{membership_id}/`
- `POST /api/v1/organizations/invitations/accept/`

Users can belong to many organizations. Role grants are scoped to the organization. Non-platform users cannot grant `platform_admin` or `super_admin`; users cannot grant themselves privileged roles.

Invitation acceptance is authenticated and single-use. The request body is `{ "token": "..." }`. Expired, revoked, or already accepted invitations fail. The authenticated user's email must match the invited email unless the user is a platform admin. Acceptance creates or reactivates an organization membership, writes an audit log, and tracks `organization_member_added`.

## Permissions

Use `PermissionService` for platform admin checks, organization management checks, course ownership, lesson access, job ownership, verification permissions, and private asset access.

The central permission service also covers organization visibility, membership management, job publishing, company profile management, portfolio/resume ownership, certificate management, verification records, payments, and entitlement subjects.

## Entitlements

Use `EntitlementService` to answer access questions for paid courses, AI tutor, certificate downloads, recruiter capabilities, organization reports, and premium resume analysis.

Entitlement checks are provider-neutral. Stripe webhooks and future billing providers should update local subscription or entitlement records; views should ask `EntitlementService` rather than checking provider state directly.

Recruiter monetization starts with `OrganizationRecruiterEntitlement`, which stores:

- `max_recruiter_seats`
- `can_post_jobs`
- `can_search_candidates`
- `can_view_candidate_profiles`
- optional `starts_at` and `ends_at`

Active recruiter seats are counted from active organization memberships with role `recruiter`. Company admins can invite recruiters only when the organization has an active entitlement and an available seat. Platform admins can override operationally.

## Recruiter Jobs

Jobs are owned by an organization and optionally a posting user. Recruiter job APIs live under `/api/v1/jobs/organizations/{organization_id}/`:

- `GET /api/v1/jobs/organizations/{organization_id}/`
- `POST /api/v1/jobs/organizations/{organization_id}/`
- `PATCH /api/v1/jobs/organizations/{organization_id}/{job_id}/`
- `POST /api/v1/jobs/organizations/{organization_id}/{job_id}/publish/`
- `POST /api/v1/jobs/organizations/{organization_id}/{job_id}/archive/`

Recruiters can manage jobs only for organizations where they hold an active recruiter role and the organization has recruiter posting entitlement. Company admins can manage organization jobs when entitled. Platform admins can manage all jobs. Job creation, publish, and archive actions are audited; publish also tracks `job_published`.

## Candidate Visibility

Recruiter candidate views require an `organization_id` query parameter and an organization entitlement that allows candidate search and profile views. Candidate profiles must be public or explicitly unlocked for that organization. Recruiter views use the public/recruiter portfolio serializers and do not expose private documents or verification documents. Successful recruiter views track `recruiter_viewed_candidate`.

## Recruiter Workflow

Revenue Pass 2 adds a recruiter hiring workflow around organization-owned jobs.

Applications are stored in `JobApplication` and move through these stages:

- `draft`
- `applied`
- `under_review`
- `shortlisted`
- `assessment`
- `interview_scheduled`
- `interview_completed`
- `offer_sent`
- `offer_accepted`
- `offer_declined`
- `rejected`
- `withdrawn`

Each stage transition creates an audit log, analytics event, application activity, and timeline entry. Candidate-visible transitions create notifications. Candidates can withdraw their own applications; recruiters and company admins manage organization applications through `PermissionService`.

Primary application and pipeline APIs:

- `POST /api/v1/jobs/{job_id}/apply/`
- `POST /api/v1/jobs/applications/{application_id}/withdraw/`
- `GET /api/v1/jobs/organizations/{organization_id}/dashboard/`
- `GET /api/v1/jobs/organizations/{organization_id}/pipeline/`
- `GET /api/v1/jobs/organizations/{organization_id}/applications/{application_id}/timeline/`
- `POST /api/v1/jobs/organizations/{organization_id}/applications/{application_id}/stage/`
- `POST /api/v1/jobs/organizations/{organization_id}/applications/{application_id}/assign/`
- `GET|POST /api/v1/jobs/organizations/{organization_id}/applications/{application_id}/notes/`
- `POST /api/v1/jobs/organizations/{organization_id}/applications/bulk-stage/`
- `POST /api/v1/jobs/organizations/{organization_id}/applications/bulk-archive/`
- `POST /api/v1/jobs/organizations/{organization_id}/applications/bulk-reject/`

The recruiter dashboard exposes job counts, application counts, stage distribution, upcoming interviews, recruiter seats, candidate unlock usage, analytics summary, and recent recruiter activity.

Candidate search lives at `GET /api/v1/jobs/organizations/{organization_id}/candidates/`. It supports filters for skills, experience, location, country, city, language, career interests, remote preference, verification status, portfolio availability, resume availability, work authorization, and pagination.

Saved candidates and talent pools are organization-scoped:

- `GET|POST /api/v1/jobs/organizations/{organization_id}/saved-candidates/`
- `DELETE /api/v1/jobs/organizations/{organization_id}/saved-candidates/{candidate_id}/`
- `GET|POST /api/v1/jobs/organizations/{organization_id}/talent-pools/`

Saving candidates requires recruiter candidate-search entitlement and candidate profile-view entitlement. Candidate saves track `candidate_saved`.

## Interviews

Interview scheduling uses:

- `Interview`
- `InterviewParticipant`
- `InterviewFeedback`
- `InterviewScorecard`

Supported interview types are `online`, `phone`, and `onsite`. Interviews include status, meeting link, location, scheduled start/end, and timezone.

Interview APIs:

- `GET|POST /api/v1/jobs/organizations/{organization_id}/interviews/`
- `PATCH /api/v1/jobs/organizations/{organization_id}/interviews/{interview_id}/`
- `POST /api/v1/jobs/organizations/{organization_id}/interviews/{interview_id}/feedback/`
- `POST /api/v1/jobs/organizations/{organization_id}/interviews/{interview_id}/scorecard/`

Scheduling an interview moves the application to `interview_scheduled`, records audit and analytics, writes timeline entries, and notifies the candidate. Completing an interview tracks `interview_completed` and moves the application to `interview_completed`.

## Recruiter Frontend

Recruiter Frontend Pass 1 adds browser pages for the Revenue Pass 2 APIs. Recruiter navigation appears only for users with recruiter-like roles: `recruiter`, `company_admin`, `platform_admin`, `super_admin`, or `admin`.

Frontend routes:

- `/recruiter/dashboard`
- `/recruiter/jobs`
- `/recruiter/jobs/new`
- `/recruiter/jobs/{job_id}`
- `/recruiter/jobs/{job_id}/edit`
- `/recruiter/pipeline`
- `/recruiter/applications/{application_id}`
- `/recruiter/candidates`
- `/recruiter/saved-candidates`
- `/recruiter/interviews`

The recruiter shell loads `/api/v1/organizations/` and selects the requested `?org={organization_id}` or the first available organization. Pages show explicit states for unauthenticated users, non-recruiter users, missing organizations, loading, empty data, and API errors.

Known frontend limitations:

- There is no dedicated organization switcher settings page yet.
- Candidate search exposes education, availability, and expected salary filters, but the current backend does not yet store those as first-class candidate fields.
- Application detail is derived from the pipeline list plus timeline/notes/interviews endpoints because there is not yet a single application-detail endpoint.
- Interview scheduling has no calendar integration.
- Candidate unlock is represented by backend state; there is not yet a separate paid unlock purchase flow in the UI.

## Webhooks

All webhook endpoints must require a configured secret or provider signature. Production fails closed if the secret is missing.

## Uploads

Upload metadata validation lives in `UploadValidationService`. Private verification documents are uploaded to the private verification bucket and exposed only through short-lived signed URLs.

## Audit Logs

Audit records are append-only. They include actor, action, target, organization, IP address, user agent, timestamp, and metadata.

Audit logs are registered in Django admin as read-only records. Current privileged action events include organization creation, member invitation, member role changes, member removal, course publishing, certificate issuance, verification decisions, payment/subscription updates, and admin security actions.

## Platform Verification Workbench

Super admins use `/platform/verification` to review instructor, recruiter, and organization verification requests. The page is backed by dedicated platform endpoints:

- `GET /api/v1/platform/verification/`
- `GET /api/v1/platform/verification/{request_id}/`
- `POST /api/v1/platform/verification/{request_id}/{action}/`

Supported actions are `assign`, `approve`, `reject`, and `more_info`. Rejection and more-information requests require a reviewer reason of at least 10 characters. The action path reuses the verification service so subject verification status, verification action history, trust events, notifications, and audit logs remain consistent with existing verification APIs.

The detail endpoint returns verification request metadata, active document metadata, and action history. It intentionally uses the safe verification document serializer, so private `s3_bucket` and `s3_key` values are never exposed to the browser.

Manual test:

1. Sign in as `admin@tcareer.local`.
2. Open `/platform/dashboard`, then `Verification workbench`.
3. Filter by status, subject type, priority, and assignment.
4. Select a request, inspect applicant notes, document metadata, and action history.
5. Assign the request to yourself.
6. Approve one request and confirm audit history updates.
7. Reject or request more information with a clear reason and confirm short reasons are blocked.

## Analytics Events

Analytics events are intentionally simple relational records for now. They can later be mirrored into a queue or warehouse without changing product code that calls `AnalyticsService.track`.

Initial event names include `course_started`, `lesson_completed`, `resume_uploaded`, `portfolio_published`, `job_applied`, `certificate_earned`, `subscription_purchased`, `ai_tutor_used`, `recruiter_viewed_candidate`, and `organization_member_added`.

Recruiting event names include `job_created`, `job_published`, `application_created`, `application_stage_changed`, `candidate_saved`, `candidate_unlocked`, `interview_scheduled`, `interview_completed`, `offer_sent`, `offer_accepted`, and `offer_declined`. Reusable recruiter analytics helpers live in `AnalyticsService`.

## Manual Revenue Tests

1. Create a company organization.
2. Create an `OrganizationRecruiterEntitlement` with at least one recruiter seat and job/candidate flags enabled.
3. Add or invite a recruiter under the seat limit.
4. Accept the invitation with `POST /api/v1/organizations/invitations/accept/`.
5. Create a draft job with `POST /api/v1/jobs/organizations/{organization_id}/`.
6. Publish it with `POST /api/v1/jobs/organizations/{organization_id}/{job_id}/publish/`.
7. View a candidate with `GET /api/v1/careers/portfolio/{username}/recruiter-view/?organization_id={organization_id}`.
8. Apply to the job with `POST /api/v1/jobs/{job_id}/apply/`.
9. Move the application through the pipeline with `POST /api/v1/jobs/organizations/{organization_id}/applications/{application_id}/stage/`.
10. Schedule an interview with `POST /api/v1/jobs/organizations/{organization_id}/interviews/`.
11. Save a candidate with `POST /api/v1/jobs/organizations/{organization_id}/saved-candidates/`.
12. Confirm audit, analytics, timeline, activity, and notification records were created.

## Manual Recruiter Frontend Tests

1. Sign in as a user with `recruiter` or `company_admin` role and an active organization membership.
2. Open `/recruiter/dashboard` and confirm job, application, seat, unlock, stage, status, funnel, upcoming interview, and recent activity summaries render.
3. Open `/recruiter/jobs`, create a draft job, edit it, publish it, archive it, and open its detail page.
4. Apply to the job as a candidate, then return as recruiter and open `/recruiter/pipeline`.
5. Search the pipeline, move the application between stages, confirm stage movement shows loading and rolls back on failure, bulk reject/archive selected applications, and open application detail.
6. Add an internal note, assign a recruiter, assign a hiring manager, schedule an interview, reject/archive the application, and verify timeline, activity, attachment, feedback, scorecard, and audit-style history sections.
7. Open `/recruiter/candidates`, filter candidates, confirm locked candidates show unlock controls, unlock an eligible candidate, verify entitlement-denied states, and save one with a label and private note.
8. Open `/recruiter/saved-candidates`, create a talent pool, and remove a saved candidate.
9. Open `/recruiter/interviews`, update interview status, add feedback, and add a scorecard.
10. Use the organization switcher on recruiter pages, refresh the browser, and verify the selected organization persists through `localStorage` and the `?org=` query.
11. Open `/recruiter/settings` and verify organization profile, members, roles, seats, unlock usage, entitlement summary, pending invitations, and audit activity render.
12. As a permitted company admin, invite a recruiter, change a member role, and remove a member. As a plain recruiter, verify management controls are disabled or hidden.

## Recruiter Frontend Pass 2

Recruiter pages share an organization switcher in `RecruiterShell`. The selected organization is read from `?org=`, then `localStorage`, then the first organization available to the signed-in recruiter. Navigation links preserve the selected organization query so dashboard, jobs, pipeline, candidate search, saved candidates, interviews, and settings stay scoped consistently.

The `/recruiter/settings` page is the recruiter administration surface. It shows organization profile metadata, active members and scoped roles, recruiter seat usage, candidate unlock usage, entitlement flags, pending invitations, and recent audit activity. Users with organization management permission can invite recruiters, change member roles, and remove members.

Candidate search now distinguishes locked and unlocked candidates. Recruiters can attempt an unlock from search results. Successful unlocks refresh the candidate card state. Denied unlocks show a permission or entitlement error without starting a payment flow.

Application detail uses the aggregate application endpoint at `GET /api/v1/jobs/organizations/{organization_id}/applications/{application_id}/`. The page shows candidate and job context, current stage, timeline, notes, attachments, application activity, interviews, feedback, scorecards, and audit-style history. Recruiter actions are grouped on the page: change stage, assign recruiter, assign hiring manager, add note, schedule interview, reject, and archive.

Pipeline movement remains select-based because the project does not currently include a drag-and-drop dependency. Stage changes optimistically update the board, show a loading state, and restore the previous board if the API call fails.

Recruiter analytics stay lightweight and dependency-free. The dashboard renders cards and simple bar charts for applications by stage, jobs by status, offer funnel, candidate unlock usage, upcoming interviews, and recent activity over time.

## Recruiter Demo Data

Use the recruiter demo commands to prepare a reliable local hiring-marketplace story without manually creating data.

Seed:

```powershell
$env:TCAREER_DEMO_PASSWORD='ChooseALocalDemoPassword123!'
python manage.py seed_recruiter_demo
```

Reset:

```powershell
python manage.py reset_recruiter_demo
```

Outside `DEBUG=True`, both commands are blocked unless `ALLOW_RECRUITER_DEMO_COMMANDS=True` is set. Demo users require `TCAREER_DEMO_PASSWORD` outside DEBUG. In DEBUG only, the command falls back to `DemoPass123!` if no password is supplied. Do not enable the fallback in production.

Demo accounts:

- `company.admin@tcareer.demo`
- `recruiter@tcareer.demo`
- `recruiter2@tcareer.demo`
- `student@tcareer.demo`
- `student2@tcareer.demo`
- `student3@tcareer.demo`
- `student4@tcareer.demo`
- `student5@tcareer.demo`
- `university.admin@tcareer.demo`

The seeded company is `TechNova Africa`; the seeded university is `Conakry Digital University`. The company has recruiter entitlements, recruiter seats, candidate unlocks, talent pools, saved candidates, jobs, applications, interviews, feedback, scorecards, notifications, analytics events, and audit logs. Demo records use deterministic demo emails/slugs and `metadata.source` or `payload.source` set to `recruiter_demo_seed` where the model supports metadata.

Seeded jobs:

- Junior Data Analyst
- Backend Django Developer
- AI Product Intern
- Career Success Associate

Seeded applications span `Applied`, `Under Review`, `Shortlisted`, `Assessment`, `Interview Scheduled`, `Interview Completed`, `Offer Sent`, and `Rejected` so dashboard charts and the pipeline board are meaningful immediately.

Recommended demo walkthrough:

1. Sign in as `company.admin@tcareer.demo`.
2. Open `/recruiter/dashboard` and show jobs by status, application stages, offer funnel, unlock usage, and recent activity.
3. Open `/recruiter/settings` and show organization profile, members, recruiter seats, entitlement, pending invitations, and audit activity.
4. Switch to `/recruiter/jobs`, open each job, then open applications for a job.
5. Open `/recruiter/pipeline`, move one application to a new stage, and show rollback-ready loading behavior.
6. Open an application detail page and show candidate context, notes, attachments, timeline, activity, interviews, feedback, scorecards, and audit-style history.
7. Open `/recruiter/candidates`, show locked/unlocked candidate states, save a candidate, and demonstrate unlock entitlement behavior.
8. Open `/recruiter/saved-candidates` and show the demo shortlist talent pool.
9. Open `/recruiter/interviews`, update an interview status, add feedback, and add a scorecard.
10. Sign in as `university.admin@tcareer.demo` to explain university support as the next expansion path.

## Student Career Pass 1

Student career work now centers on the learner/job-seeker experience:

- `/dashboard` is a career dashboard with profile, resume, and portfolio completion; skills; certificates; active courses; applications; application timeline; upcoming interviews; saved jobs; recommended jobs; recruiter activity; and AI usage placeholders.
- `/jobs` is the modern job discovery surface with search, skills, category, country, city, company, work mode, experience, salary, posted-date, verification, pagination, and sorting filters.
- `/jobs/{job_id}` is the student job detail and apply surface. It shows company and organization context, description, responsibilities, requirements, skills, salary, location, recruiter, deadline, verification badge, related jobs, application status, draft save, direct apply, resume/portfolio selection context, and save-job action.
- `/applications` shows the student's application list, draft submission, withdrawal, timeline, interview, and attachment history.
- `/saved-jobs` shows saved jobs, collections, favorite-company foundation, recently viewed foundation, and job-alert API foundation.
- `/career-profile` is the public career identity hub for headline, about, skills, education/resume summary, experience, projects, certificates, links, availability, privacy, verification readiness, recruiter views, and AI analysis placeholders.

Backend endpoints added for the student flow:

- `GET /api/v1/jobs/student/dashboard/`
- `GET /api/v1/jobs/student/applications/`
- `GET /api/v1/jobs/student/applications/{application_id}/`
- `POST /api/v1/jobs/student/applications/{application_id}/submit/`
- `GET|POST /api/v1/jobs/student/saved/`
- `DELETE /api/v1/jobs/student/saved/{job_id}/`
- `GET|POST /api/v1/jobs/student/collections/`
- `GET /api/v1/jobs/student/recently-viewed/`
- `GET|POST /api/v1/jobs/student/alerts/`
- `POST /api/v1/jobs/{job_id}/draft/`

The existing `GET /api/v1/jobs/`, `GET /api/v1/jobs/{job_id}/`, `POST /api/v1/jobs/{job_id}/apply/`, and application withdrawal endpoints remain compatible. Job list filtering was expanded, and job detail now records `job_viewed` analytics plus recently viewed job records for authenticated students.

Student analytics currently tracked:

- `job_viewed`
- `job_saved`
- `job_applied`
- `application_withdrawn`
- existing recruiter-side profile view/unlock events shown on the student dashboard

Manual student career test:

1. Sign in as a student.
2. Open `/dashboard` and verify completion cards, applications, interviews, saved jobs, recommended jobs, recruiter activity, and AI placeholders.
3. Open `/jobs`, search and filter by skill, location, work mode, experience, salary, company, and posted date.
4. Open `/jobs/{job_id}`, save the job, save a draft application, submit it, and confirm status appears.
5. Open `/applications`, inspect the timeline, submit a draft if present, and withdraw a non-terminal application.
6. Open `/saved-jobs`, create a collection, remove a saved job, and confirm the job-alert foundation note.
7. Open `/career-profile`, `/resume`, and `/portfolio` to review profile completeness, resume content, portfolio projects, links, privacy, and public sharing.

## Student Career Pass 2

The student career layer now supports real multi-resume workflows, portfolio project media, job alert delivery, and scored recommendations.

Multi-resume system:

- A student can own many `CareerResume` records.
- Exactly one active resume can be marked default; setting a resume as default clears the flag from the user's other resumes.
- Resume edits create `ResumeVersion` snapshots.
- Resume files are represented by `ResumeFile` records and default to private.
- `ResumeAnalytics` tracks recruiter views, downloads, and application usage.
- `JobApplication.selected_resume` stores the resume selected when a student saves a draft or applies.

Resume routes:

- `/resumes`
- `/resumes/new`
- `/resumes/{resumeId}`
- `/resumes/{resumeId}/edit`

Resume endpoints:

- `GET|POST /api/v1/careers/resumes/`
- `GET|PATCH /api/v1/careers/resumes/{resume_id}/`
- `POST /api/v1/careers/resumes/{resume_id}/duplicate/`
- `POST /api/v1/careers/resumes/{resume_id}/default/`
- `POST /api/v1/careers/resumes/{resume_id}/archive/`
- `POST /api/v1/careers/resumes/{resume_id}/files/`
- `POST /api/v1/careers/resumes/{resume_id}/download/`

Portfolio media:

- Portfolio projects can now have ordered media records for images, videos, and documents.
- Project media has its own visibility flag.
- Private project media is visible to the owner but filtered from public portfolio responses.
- `/career-profile` now includes project creation, featured toggles, media URL entry, visibility control, public preview, and a portfolio analytics summary.

Portfolio media endpoints:

- `POST /api/v1/careers/portfolio/me/projects/{project_id}/media/`
- `PATCH|DELETE /api/v1/careers/portfolio/me/projects/{project_id}/media/{media_id}/`

Job alerts:

- `JobAlertService` matches active alerts against active jobs.
- `python manage.py run_job_alerts` creates `new_job_match` notifications with email-ready payloads.
- Alerts are non-spamming: a user is notified only once per alert/job pair.
- Matching emits `job_alert_matched` analytics.
- Email sending remains intentionally out of scope for this pass.

Recommendation scoring:

- Student dashboard recommendations score jobs using skills, location, remote preference, experience level, desired role, profile completeness, and application history.
- Recommendations include explanation strings such as `Matches 1 of your skills` and `Remote role matching your preference`.
- Jobs already in the student's application history are de-prioritized but can still appear if there are few active matches.

Student analytics added:

- `resume_created`
- `resume_updated`
- `resume_downloaded`
- `resume_used_for_application`
- `portfolio_project_created`
- `portfolio_project_updated`
- `job_alert_matched`

Manual Student Career Pass 2 test:

1. Sign in as a student and open `/resumes`.
2. Create two resumes, set one as default, duplicate one, archive one, and verify the default badge.
3. Open a resume detail page, add a private resume file URL, click Download, and confirm usage analytics increment.
4. Open `/jobs/{job_id}`, choose a resume in the application form, save a draft, then submit it.
5. Open `/career-profile`, create a project, mark it featured, add image/video media, change portfolio visibility, and open the public preview.
6. Create a job alert through the existing student alerts API, run `python manage.py run_job_alerts`, and verify a `new_job_match` notification is created once.
7. Open `/dashboard` and confirm recommended jobs include match explanations.

## Student Career Pass 3

Student career production-readiness now adds storage-backed uploads, application preview, richer public profiles, alert delivery metadata, and student analytics cards.

Storage-backed resume uploads:

- `ResumeFile` keeps the existing `file_url` compatibility field and now also supports a private Django storage `file`.
- Resume uploads accept PDF, DOC, and DOCX files up to 5 MB.
- Resume files are always stored as private records.
- Resume downloads are authorized for the owner, platform/staff admins, and entitled recruiter access with an organization context.
- Download events create `ResumeAnalytics.DOWNLOADED` and `resume_downloaded` analytics.

Portfolio media uploads:

- `PortfolioProjectMedia` keeps URL-based media compatibility and now supports uploaded image files.
- Uploaded project images accept PNG, JPG, JPEG, and WEBP files up to 8 MB.
- Video remains URL-based until a future video processing/storage pass.
- Project media supports ordering, featured media, and visibility controls.
- Private media is filtered from public profile responses.

Public profile behavior:

- `/u/{username}` now presents profile photo, headline, about, skills, work preferences, open-to-work status, verification badge, featured projects, media links, certificates, education, experience, completed courses, and career tracks.
- Public profiles only expose default resume education/experience content, not private resume files.
- Empty states are shown when the profile is still sparse.

Application preview:

- `POST /api/v1/jobs/{job_id}/preview/` returns the job, company, selected resume summary, portfolio link context, cover letter, answer placeholder data, and profile completion summary.
- The job detail page now supports Preview, Save draft, and Apply as separate actions.

Job alert delivery:

- `JobAlert` tracks `last_run_at`, `last_matched_count`, and `total_matched_count`.
- `python manage.py run_job_alerts` creates notifications with email-ready payloads but still does not send email.
- Duplicate prevention remains alert/job based, so repeated command runs do not spam students.

Student analytics:

- `/dashboard` now includes cards for profile views, recruiter views, resume downloads, portfolio views, saved jobs, job alert matches, recommendation clicks, and tracked applications.
- Recommendation clicks are tracked through `POST /api/v1/jobs/{job_id}/recommended-click/`.

Manual Student Career Pass 3 test:

1. Open `/resumes/{resumeId}` and upload a PDF/DOC/DOCX file. Try an invalid extension and confirm it is rejected.
2. Download the resume and confirm the file opens or returns the compatible URL, then refresh and confirm download analytics increment.
3. Open `/career-profile`, upload an image to a project, add a video URL, feature a project, and confirm the public preview only shows public media.
4. Open `/u/{username}` and review profile photo, verification badge, about, skills, education, experience, certificates, projects, media, and empty states.
5. Open `/jobs/{jobId}`, choose a resume, write a cover letter, click Preview, edit, save draft, then apply.
6. Run `python manage.py run_job_alerts` twice and confirm only one notification is created for the same alert/job pair.
7. Open `/dashboard` and review the analytics cards.

## Notification And Storage Hardening Pass

Email delivery foundation:

- `EmailDelivery` records are created from the existing notification flow for job alert matches, interview scheduled/updated, application status changes, offers, recruiter invitations, and organization invitation acceptance.
- Delivery records store recipient, subject, body, template key, metadata, delivery status, retry count, last error, and sent timestamp.
- SMTP sending remains intentionally conservative. Delivery records are created as pending and only sent by the provider command when SMTP is configured.
- Console email backend is treated as not configured for provider sends. Locmem remains usable for tests.

Job alert delivery:

- `python manage.py run_job_alerts` creates notifications plus email delivery records.
- `python manage.py run_job_alerts --dry-run` evaluates matches without creating notifications, email delivery rows, analytics, or alert counters.
- `python manage.py run_job_alerts --limit 50` caps total matches for one command run.
- Alert/job duplicate prevention still prevents repeated notifications for the same alert and job.
- Alerts continue tracking `last_run_at`, `last_matched_count`, and `total_matched_count`.

Interview notifications:

- Scheduling an interview notifies the candidate and assigned recruiter when applicable.
- Updating an interview notifies the candidate and assigned recruiter when applicable.
- Interview notifications create email delivery records and analytics events.

Application questions:

- Jobs can now have application questions with these types: `short_text`, `long_text`, `yes_no`, `multiple_choice`, `number`, and `url`.
- Recruiters can manage questions through organization-scoped job question endpoints.
- Students answer questions during preview, draft save, and application submit.
- Recruiter application detail and student application detail include submitted answers.

Application question endpoints:

- `GET|POST /api/v1/jobs/organizations/{organization_id}/{job_id}/questions/`
- `PATCH|DELETE /api/v1/jobs/organizations/{organization_id}/{job_id}/questions/{question_id}/`

Private storage access:

- Resume downloads support owner access, staff/platform access, and recruiter access when an organization context has an unlocked candidate profile and valid recruiter entitlement.
- Private resume downloads continue to track download analytics.
- File validation uses the shared upload validation service.
- Local storage returns local media URLs. S3-ready storage uses the same authorization layer and can return presigned private download URLs when AWS storage settings are configured.

Student analytics:

- `/dashboard` now shows grouped application status chips in addition to analytics cards.
- Recommendation clicks remain tracked via `recommended_job_viewed`.

Manual hardening test:

1. Create application questions on a recruiter-owned job and verify they appear on `/jobs/{jobId}`.
2. Answer questions, click Preview, save a draft, submit, then review answers in `/applications`.
3. Open recruiter application detail and confirm submitted answers are visible.
4. Schedule and update an interview; confirm notifications and email delivery records exist.
5. Run `python manage.py run_job_alerts --dry-run` and confirm no records are created.
6. Run `python manage.py run_job_alerts --limit 50` and confirm notifications/email delivery records are created once.
7. Try private resume download as owner, platform admin, locked recruiter, and unlocked recruiter.

## Email And Storage Provider Pass

Email provider operations:

- `EmailDeliveryService` now supports `pending`, `sent`, `failed`, `retrying`, and `cancelled` delivery operations while preserving older `queued` and `skipped` rows for compatibility.
- Provider sending is isolated in `EmailDeliveryService.send_email_delivery(delivery_id)`.
- `bulk_process_pending(limit=50)` processes pending/queued/retrying rows.
- `retry_failed(limit=50)` retries failed rows and respects `EMAIL_DELIVERY_MAX_RETRIES`.
- Sent deliveries are never sent again. Missing SMTP configuration marks the delivery failed with `last_error`.
- Successful sends store `sent_at`; provider message id storage is available through `provider_message_id`.

Email command:

- `python manage.py process_email_deliveries`
- `python manage.py process_email_deliveries --limit 50`
- `python manage.py process_email_deliveries --retry-failed`
- `python manage.py process_email_deliveries --dry-run`

SMTP variables:

- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_USE_TLS`
- `DEFAULT_FROM_EMAIL`
- `EMAIL_DELIVERY_MAX_RETRIES`

Email templates:

- Simple structured templates are defined for `job_alert_match`, `interview_scheduled`, `interview_updated`, `application_status_changed`, `offer_received`, `organization_invitation`, and `recruiter_invitation`.
- Notification payload values can still override or supplement email metadata.

Email admin operations:

- `EmailDelivery` is visible in Django admin with recipient, template, status, retry count, last error, created timestamp, and sent timestamp.
- The admin view is read-only for direct edits and includes a safe retry action for selected unsent deliveries.

Signed private downloads:

- Resume file authorization remains in the careers API.
- After authorization, `generate_private_download_url` returns compatible `file_url`, a local storage URL, or an S3 presigned URL depending on storage configuration.
- Access rules cover owner, staff/platform admin, unlocked recruiter, and locked recruiter denial.

Recruiter application question UI:

- Recruiters can manage job application questions from `/recruiter/jobs/{jobId}` and `/recruiter/jobs/{jobId}/edit`.
- The UI supports list, create, edit, soft remove, required toggle, question type, multiple-choice options, and simple ordering.

Manual provider test:

1. Configure local email with locmem or SMTP settings and create a job alert/interview notification.
2. Run `python manage.py process_email_deliveries --dry-run` and confirm no delivery status changes.
3. Run `python manage.py process_email_deliveries --limit 50` and confirm pending rows become sent when email is configured.
4. Switch to console backend or remove SMTP settings, process a pending delivery, and confirm it becomes failed with `last_error`.
5. Mark a delivery failed and run `python manage.py process_email_deliveries --retry-failed`.
6. As a recruiter, open `/recruiter/jobs/{jobId}/edit`, create questions, reorder them, mark one required, and soft remove one.
7. Try resume download as owner, platform admin, locked recruiter, and unlocked recruiter.

## Notification UX And Trust Controls Pass

Notification preferences:

- `NotificationPreference` stores per-user channel settings by category.
- Supported categories are `job_alerts`, `applications`, `interviews`, `offers`, `organization_invites`, `recruiter_invites`, `course_updates`, `certificates`, `marketing`, and `security`.
- Supported channels are in-app and email.
- Security preferences are always forced enabled and cannot be disabled through API updates.
- Existing notifications and email deliveries are backfilled into categories during migration where notification type is known.

Suppression and unsubscribe:

- `EmailSuppression` blocks non-security emails by user/email and category.
- Security notifications bypass suppression.
- Authenticated users can unsubscribe and resubscribe by category.
- `NotificationUnsubscribeToken` stores hashed, expiring unsubscribe tokens for non-security email flows.
- Suppressed or preference-disabled emails create cancelled delivery records rather than disappearing silently.

Delivery lifecycle:

- `EmailDelivery` now stores category, plaintext body, HTML body, status, retry count, provider id, created timestamp, sent timestamp, failed timestamp, and last error.
- User-facing delivery history is exposed through `/api/v1/notifications/delivery-history/`.
- Admin can filter delivery records by category, template, and status, retry unsent rows, or cancel pending rows.

Branded templates:

- Reusable plaintext and HTML templates exist for job alerts, interviews, application status, offers, organization invitations, recruiter invitations, certificates, and security notifications.
- HTML templates are intentionally simple and branding-ready; advanced MJML/React email rendering is a future enhancement.

Trust and privacy controls:

- `UserPrivacySettings` stores student privacy controls: public profile, recruiter resume visibility, recruiter portfolio visibility, open to work, recruiter contact, analytics, and AI analysis.
- `/api/v1/auth/privacy/` supports GET and PATCH for authenticated users.
- The older `is_public_profile` field remains compatible and is synchronized when profile updates change it.

Recruiter visibility rules:

- Candidate search only returns candidates with public profile visibility enabled.
- Hidden resumes cannot be downloaded by recruiters, even when a candidate was previously unlocked.
- Hidden portfolios return not found in recruiter portfolio view.
- Candidate email/contact fields are hidden when `allow_recruiter_contact` is disabled.
- Direct candidate unlock is denied when the candidate profile is private.

Frontend settings:

- `/settings/notifications` lets users manage notification preferences, unsubscribe/resubscribe state, and email delivery history.
- `/settings/privacy` lets users manage recruiter visibility, open-to-work, analytics, and AI analysis controls.
- Both pages include loading, unauthenticated, empty, and error states.

Manual trust-controls test:

1. Sign in as a student and open `/settings/notifications`.
2. Disable email for job alerts and confirm a `new_job_match` notification creates a cancelled delivery record.
3. Try disabling security notifications and confirm they remain enabled.
4. Open `/settings/privacy`, disable public profile, and confirm the candidate disappears from recruiter candidate search.
5. Re-enable public profile, disable recruiter resume visibility, unlock the candidate, and confirm recruiter resume download is denied.
6. Disable recruiter portfolio visibility and confirm recruiter portfolio view returns not found.
7. Disable recruiter contact and confirm recruiter-facing application/candidate responses omit email.
8. Review Django admin EmailDelivery filters/actions for category, template, status, retry, and cancel.

## Platform Hardening Pass

Candidate visibility:

- `CandidateVisibilityService` is the authoritative service for recruiter-facing candidate access decisions.
- It evaluates profile visibility, resume visibility, portfolio visibility, recruiter contact access, unlocked candidate state, organization access, recruiter entitlement, owner access, and admin overrides.
- Candidate search, application detail, saved candidate serialization, recruiter portfolio view, resume download authorization, candidate unlock, and saved candidate service logic now route through the service.
- Recruiters must have organization access and active recruiter entitlement to view candidates. Resume download by recruiters requires the candidate to be unlocked and resume visibility enabled.

Rate limiting:

- Sensitive endpoints use scoped DRF throttles with environment-configurable rates.
- Protected scopes cover auth/login, refresh, notification preferences, unsubscribe/resubscribe, candidate unlock, recruiter search, application submission, resume download, and invitation acceptance.
- Throttled responses use the standard `rate_limited` error code and include retry wait metadata when DRF provides it.
- Throttle events are logged through the `tcareer.security.throttle` logger.

Email safety:

- `EmailDeliveryService.send_email_delivery()` rechecks account status, notification preferences, and suppressions immediately before provider dispatch.
- Delivery rows are selected with row locks where supported to reduce duplicate worker races.
- Skipped deliveries are cancelled with a concrete reason instead of failing silently.
- Missing SMTP configuration still prevents outbound email and records a failed delivery state.

Audit expansion:

- Privacy setting changes, notification preference changes, unsubscribe/resubscribe actions, resume downloads, email admin retries, and email cancellation actions create append-only audit records.
- Existing audit coverage for candidate unlocks, organization actions, interviews, job activity, certificates, and entitlement changes remains in place.

Error response standard:

- Service errors return `{ "detail": "...", "code": "..." }`.
- Validation errors return `{ "detail": "Validation failed.", "code": "validation_error", "fields": { ... } }` while preserving field errors at top level for existing clients.
- Permission, not-found, throttled, and server errors use stable `code` values.

Monitoring strategy:

- Structured loggers are now used for email processing, candidate unlock decisions, resume download decisions, job alert processing, interview scheduling, and rate-limit events.
- The log payloads are intentionally plain dictionaries so they can later be forwarded to Sentry, OpenTelemetry, CloudWatch, Datadog, or another collector.
- Privacy violations and denied access attempts are logged without exposing private document contents.

Performance improvements:

- Candidate search uses `select_related`, `prefetch_related`, page-scoped ID lookups, and batched saved/unlocked/resume checks to avoid the biggest N+1 pattern.
- Privacy read checks avoid creating settings rows in read-only list flows.
- Application detail and pipeline serializers receive organization context so they can avoid duplicated visibility decisions.
- Future caching candidates: organization entitlement summary, recruiter dashboard aggregates, notification history counts, and candidate recommendation scoring.

Manual hardening test:

1. Disable a student's public profile and confirm recruiter search no longer returns them.
2. Re-enable public profile, leave the candidate locked, and confirm recruiter resume download is denied.
3. Unlock the candidate and confirm resume download is allowed only when resume visibility is enabled.
4. Lower a throttle rate locally and confirm the protected endpoint returns `code=rate_limited`.
5. Suppress a user/category, process a pending email delivery, and confirm it is cancelled before send.
6. Change privacy and notification preferences, then confirm audit log records exist.
7. Exercise candidate search with several candidates and confirm query counts stay bounded in tests.

## Production Ops Pass 1

Cache and throttling:

- Production cache is Redis-ready through `CACHE_BACKEND=django_redis.cache.RedisCache`.
- `REDIS_URL` is the default shared Redis location for cache, Celery broker, and Celery result backend.
- `DJANGO_CACHE_LOCATION` can override the cache location independently from Celery.
- Development defaults to local memory cache unless `CACHE_BACKEND` is set explicitly.
- DRF throttling uses the Django default cache, so production throttles share counters when the default cache is Redis.

Health checks:

- `GET /api/v1/health/` returns dependency status for database, cache, storage, email, and Celery configuration.
- `GET /api/v1/health/ready/` returns `503` when critical checks fail.
- `GET /api/v1/health/live/` returns process liveness without dependency checks.
- Health responses never expose passwords, Redis URLs, SMTP credentials, bucket names, or Sentry DSNs.

Observability:

- Production Sentry setup is provider-ready and controlled by `SENTRY_DSN`, `SENTRY_ENVIRONMENT`, and `SENTRY_TRACES_SAMPLE_RATE`.
- If `SENTRY_DSN` is empty, the application runs without Sentry.
- Structured logs now cover auth failures, rate limits, email processing, candidate unlocks, resume downloads, job alerts, command completion, interview scheduling, and health-check failures.

Worker monitoring:

- `python manage.py process_email_deliveries` logs command completion with mode, limit, label, and processed count.
- `python manage.py run_job_alerts` logs summary counts for checked alerts, created matches, email-ready payloads, and dry-run state.
- Celery startup remains `celery -A tasks worker -l info`; beat remains `celery -A tasks beat -l info` when scheduled tasks are enabled.
- Worker dashboards should monitor failed email deliveries, retry counts, command runtime, queue depth, and dead-letter/retry volume.

Email idempotency:

- `EmailDeliveryService` stores deterministic `metadata.idempotency_key` values for notification-backed deliveries.
- A delivery already marked `sent` is never resent.
- A second delivery with the same sent idempotency key is cancelled before provider dispatch.
- In-progress deliveries are held in `retrying`; recently updated `retrying` deliveries are treated as already processing.
- Final account status, notification preference, and suppression checks still run immediately before send.

Audit coverage matrix:

| Domain | Current audit coverage | Known gaps |
| --- | --- | --- |
| Auth | Admin login, auth failure logging | Non-admin successful login audit intentionally omitted for volume |
| Organization | Creation, invitations, membership changes | Bulk org reporting exports |
| Privacy | Privacy settings changed | Field-level consent history beyond metadata |
| Notifications | Preference changes, unsubscribe/resubscribe | Notification read events |
| Email delivery | Admin retry/cancel, skipped delivery logging | Provider webhook events |
| Candidate search | Search performed with filter keys and result count | Per-result impression audit is too noisy |
| Candidate unlock | Unlock created/denied logging | Unlock expiry lifecycle |
| Resume download | Download audit and analytics | Provider signed-URL access callback |
| Portfolio visibility | Privacy controls and recruiter denial | Individual media access audit |
| Job posting | Create, publish, archive | Minor edit field diff |
| Application changes | Create, stage changes, archive, assignment | Attachment download audit |
| Interviews | Schedule/update/complete analytics and audit | Calendar integration events |
| Payments/entitlements | Entitlement changes from foundation | Full payment provider dispute/refund events |
| Admin actions | Email retry/cancel and security actions | Full admin object change audit |

Query-count budgets:

- Candidate search budget: 25 queries in hardening test coverage.
- Recruiter dashboard budget: 35 queries.
- Student dashboard budget: 65 queries.
- Application detail budget: 45 queries.
- Public job detail budget: 12 queries.
- Notification delivery history budget: 6 queries.
- These are guardrails against regressions. They are not final performance targets for high-scale production.

Production environment variables:

```text
SECRET_KEY
DATABASE_URL
ALLOWED_HOSTS
REDIS_URL
CACHE_BACKEND=django_redis.cache.RedisCache
DJANGO_CACHE_LOCATION
CELERY_BROKER_URL
CELERY_RESULT_BACKEND
EMAIL_BACKEND
EMAIL_HOST
EMAIL_PORT
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
EMAIL_USE_TLS
DEFAULT_FROM_EMAIL
SENTRY_DSN
SENTRY_ENVIRONMENT
SENTRY_TRACES_SAMPLE_RATE
CORS_ALLOWED_ORIGINS
CSRF_TRUSTED_ORIGINS
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
AUTH_COOKIE_SECURE=True
```

Production checklist:

1. Set production settings module and secrets through environment variables.
2. Provision Postgres with backups and connection limits.
3. Provision Redis and set `CACHE_BACKEND=django_redis.cache.RedisCache`.
4. Run migrations.
5. Verify `/api/v1/health/ready/` returns `200`.
6. Start web, Celery worker, and Celery beat processes.
7. Run `python manage.py process_email_deliveries --dry-run`.
8. Run `python manage.py run_job_alerts --dry-run --limit 10`.
9. Confirm Sentry receives a release/environment heartbeat if configured.
10. Confirm audit logs are append-only in admin.

Rollback checklist:

1. Stop job-alert and email-processing commands first to avoid duplicate side effects.
2. Drain or pause Celery workers.
3. Roll back web application release.
4. Re-run `/api/v1/health/ready/`.
5. Review email delivery rows in `retrying` or `failed`.
6. Review audit logs for privileged actions during the incident window.

## Production Ops Pass 2

Production Redis enforcement:

- Production-like deployments are identified with `DEPLOY_ENVIRONMENT=production`.
- In production, `REDIS_URL` must be set.
- In production, `CACHE_BACKEND` must use Redis and must not use local memory.
- DRF throttling must use the shared default Django cache.
- `/api/v1/health/ready/` fails when production cache safety checks fail or Redis is unreachable.
- Test and local development can continue using local memory cache by setting `DEPLOY_ENVIRONMENT=test` or using development settings.

Release tracking:

- Release metadata is configured with `APP_VERSION`, `GIT_SHA`, `DEPLOY_ENVIRONMENT`, `SENTRY_RELEASE`, `SENTRY_ENVIRONMENT`, and `SENTRY_TRACES_SAMPLE_RATE`.
- If `SENTRY_DSN` is empty, the application runs normally without Sentry.
- If `SENTRY_DSN` is set, Sentry receives release and environment metadata.
- Startup logs include non-secret release metadata through the `tcareer.release` logger.

Worker and queue monitoring:

- `GET /api/v1/health/ops/` is staff-only and returns safe operational status.
- It includes email queue counts for pending, queued, retrying, failed, sent, and cancelled deliveries.
- It includes recent failed/retrying delivery summaries with truncated errors.
- It includes release metadata and job-alert command hints.
- It intentionally does not expose email bodies, SMTP credentials, Redis URLs, DSNs, or secrets.

Email provider webhook:

- `POST /api/v1/notifications/email/provider-webhook/` accepts provider-neutral events.
- Supported events are `delivered`, `bounced`, `complained`, `opened`, `clicked`, and `failed`.
- The endpoint requires `EMAIL_WEBHOOK_SECRET` and a matching `X-TCareer-Email-Webhook-Secret` or `X-Webhook-Secret` header.
- Missing or invalid secrets fail closed with `403` and create a `provider_webhook_rejected` audit log.
- Events are idempotent by `event_id`.
- Deliveries can be identified by `delivery_id`, `provider_message_id`, or `idempotency_key`.
- Provider event metadata is stored on `EmailDelivery.metadata.provider_events`.

Provider suppression:

- `bounced` and `complained` events mark the delivery failed.
- For non-security categories, bounce and complaint events create or activate `EmailSuppression`.
- Security email categories are never suppressed automatically.
- High-risk events create `email_bounced`, `email_complained`, and `email_suppression_created` audit records where applicable.

Audit coverage closure:

| Event | Audit action |
| --- | --- |
| Failed login | `failed_login` |
| Rate limit exceeded | `rate_limit_exceeded` |
| Security notification sent | `security_notification_sent` |
| Email bounce | `email_bounced` |
| Email complaint | `email_complained` |
| Provider webhook rejected | `provider_webhook_rejected` |
| Admin email retry | `email_delivery_admin_retry` |
| Admin email cancellation | `email_delivery_cancelled` |
| Entitlement subscription purchase/update/cancel | `entitlement_subscription_*` |
| Candidate search | `candidate_search_performed` |
| Candidate unlock | `candidate_unlocked` |
| Resume download | `resume_downloaded` |

Production smoke command:

```powershell
python manage.py production_smoke_check
python manage.py production_smoke_check --fail-on-warning
```

The command checks database, cache, migration state, email readiness, storage readiness, critical settings, and Celery broker configuration. It does not print secrets.

Backup steps:

1. Confirm automated Postgres backups and point-in-time recovery are enabled.
2. Export a manual database snapshot before risky migrations.
3. Confirm object storage bucket versioning or equivalent retention.
4. Record the current `APP_VERSION`, `GIT_SHA`, and deployment artifact.
5. Verify restore instructions in a non-production environment.

Production smoke tests:

1. Run `python manage.py production_smoke_check`.
2. Open `/api/v1/health/live/`.
3. Open `/api/v1/health/ready/`.
4. Authenticate as staff and open `/api/v1/health/ops/`.
5. Submit a dry-run job alert command with `python manage.py run_job_alerts --dry-run --limit 10`.
6. Submit a dry-run email command with `python manage.py process_email_deliveries --dry-run`.
7. Send a signed test email provider webhook to a test delivery.
8. Confirm Sentry release metadata appears when `SENTRY_DSN` is configured.

## Production Ops Pass 3

Provider-specific email webhooks:

- `POST /api/v1/notifications/email/provider-webhook/?provider=ses` verifies `X-TCareer-SES-Signature` using `SES_WEBHOOK_SECRET`.
- `POST /api/v1/notifications/email/provider-webhook/?provider=sendgrid` verifies `X-Twilio-Email-Event-Webhook-Timestamp` plus `X-Twilio-Email-Event-Webhook-Signature` using `SENDGRID_WEBHOOK_SECRET`.
- `POST /api/v1/notifications/email/provider-webhook/?provider=mailgun` verifies Mailgun `timestamp`, `token`, and `signature` using `MAILGUN_WEBHOOK_SIGNING_KEY`.
- The legacy shared-secret fallback is only allowed when `EMAIL_WEBHOOK_ALLOW_SHARED_SECRET=True` and `DEPLOY_ENVIRONMENT` is not `production`.
- Production rejects shared-secret fallback even if `EMAIL_WEBHOOK_SECRET` is set.
- The SES adapter uses an app-local HMAC secret for deterministic verification. Native AWS SNS certificate validation remains a future provider adapter.

Live worker and queue monitoring:

- `/api/v1/health/ops/` remains staff-only.
- The payload now includes Celery inspect status, worker count, active task count, reserved task count, scheduled task count, Redis broker scheme, shared-cache status, email backlog, failed delivery counts, retrying delivery counts, recent delivery errors, and latest job-alert run metadata.
- Celery inspect can return `unknown` if the broker or workers are not reachable; this does not expose credentials.

Backup restore validation:

```powershell
python manage.py backup_restore_check --dry-run
python manage.py backup_restore_check --storage-probe
python manage.py backup_restore_check --fail-on-warning
```

- The command checks database visibility, migration table visibility, backup-related storage settings, audit retention settings, and restore runbook presence.
- `--storage-probe` writes and deletes a tiny probe file through Django storage.
- `--dry-run` skips storage writes.
- The command prints no secrets.

Deployment templates:

- `docker-compose.prod.yml` provides production-shaped Postgres, Redis, web, Celery worker, and Celery beat services.
- `env.example.production` documents required environment variables for database, Redis, cache, SMTP, webhook verification, Sentry, storage, cookies, CORS, audit retention, and runtime sizing.
- The production template uses `/api/v1/health/ready/` as the web health check.

Dependency advisory decision:

- The frontend high-severity production audit passes.
- The remaining PostCSS advisory is moderate and comes through Next's dependency tree.
- `npm audit fix --force` would install a breaking downgrade path, so it is intentionally not applied.
- Safe remediation is to upgrade Next/PostCSS when an upstream-compatible patch is available.

Audit retention:

- `AUDIT_RETENTION_ENABLED` defaults to `False`.
- `AUDIT_RETENTION_DAYS` defaults to `0`.
- No automatic audit deletion is enabled.
- Before enabling retention, export audit logs to durable storage, define legal hold behavior, and document customer compliance requirements.

Production Pass 3 smoke tests:

1. Run `python manage.py production_smoke_check --fail-on-warning`.
2. Run `python manage.py backup_restore_check --dry-run`.
3. Run `python manage.py backup_restore_check --storage-probe` in staging.
4. Confirm `/api/v1/health/ready/` returns `200`.
5. Sign and send SES, SendGrid, and Mailgun test webhook payloads in staging.
6. Confirm production rejects shared-secret webhook fallback.
7. Open `/api/v1/health/ops/` as staff and confirm Celery and Redis broker visibility.
8. Run frontend lint and confirm no warnings.

## Enterprise Platform Pass 1

Organization console:

- `/organization/dashboard` shows enterprise health, hierarchy counts, learning metrics, hiring metrics, and recent audit activity.
- `/organization/settings` shows the organization profile, members, and pending invitations.
- `/organization/departments`, `/organization/teams`, and `/organization/cohorts` manage organization-scoped hierarchy records and member assignments.
- `/organization/import` previews and commits CSV imports.
- `/organization/export` generates scoped CSV exports and records export jobs.
- `/organization/branding` manages logo, banner, colors, support contact, time zone, and language metadata.
- `/organization/policies` manages security, visibility, invitation, session, domain, and notification defaults.
- `/organization/analytics` summarizes learner, recruiter, hiring, placement, certificate, and health signals.

Backend API groups:

- `GET /api/v1/organizations/{organization_id}/enterprise/dashboard/`
- `GET/PATCH /api/v1/organizations/{organization_id}/enterprise/settings/`
- `GET/PATCH /api/v1/organizations/{organization_id}/enterprise/branding/`
- `GET/PATCH /api/v1/organizations/{organization_id}/enterprise/policies/`
- `GET/POST /api/v1/organizations/{organization_id}/enterprise/departments/`
- `GET/PATCH/DELETE /api/v1/organizations/{organization_id}/enterprise/departments/{department_id}/`
- `POST /api/v1/organizations/{organization_id}/enterprise/departments/{department_id}/members/`
- `GET/POST /api/v1/organizations/{organization_id}/enterprise/teams/`
- `GET/PATCH/DELETE /api/v1/organizations/{organization_id}/enterprise/teams/{team_id}/`
- `POST /api/v1/organizations/{organization_id}/enterprise/teams/{team_id}/members/`
- `GET/POST /api/v1/organizations/{organization_id}/enterprise/cohorts/`
- `GET/PATCH/DELETE /api/v1/organizations/{organization_id}/enterprise/cohorts/{cohort_id}/`
- `POST /api/v1/organizations/{organization_id}/enterprise/cohorts/{cohort_id}/members/`
- `POST /api/v1/organizations/{organization_id}/enterprise/imports/`
- `GET/POST /api/v1/organizations/{organization_id}/enterprise/exports/`
- `GET /api/v1/organizations/{organization_id}/enterprise/analytics/`

Data model:

- `OrganizationProfile` stores branding, support, locale, and extensible enterprise metadata.
- `OrganizationPolicy` stores security, visibility, invitation, session, domain, notification, and digest defaults.
- `Department`, `OrganizationTeam`, and `Cohort` represent enterprise hierarchy and training cohorts.
- `DepartmentMember`, `TeamMember`, and `CohortMember` attach existing organization memberships to hierarchy records.
- `BulkImportJob` stores import preview rows, validation errors, source filename, status, and counts.
- `DataExportJob` stores export type, format, row count, status, metadata, and actor.

Permission flow:

- All enterprise endpoints require authentication.
- Read/report endpoints use `PermissionService.can_view_organization`.
- Mutating endpoints use `PermissionService.can_manage_organization`.
- Member assignment validates that the target membership belongs to the same organization.
- Platform admins retain override capability through `PermissionService`.

CSV import:

- Supported import types are `students`, `recruiters`, `instructors`, `employees`, `departments`, and `teams`.
- `commit=False` creates a preview job and does not change users or hierarchy records.
- `commit=True` creates or activates organization memberships and upserts departments or teams.
- Import jobs are audited as previewed or completed.

Exports:

- CSV exports are generated inline for students, recruiters, applications, certificates, courses, organization profile, analytics, and audit logs.
- XLSX requests create a queued-style `DataExportJob` placeholder for later async export generation.
- Export generation is audited.

Manual testing:

1. Sign in as a company admin or university admin.
2. Open `/organization/dashboard`.
3. Create a department, team, and cohort.
4. Assign an existing organization member to each hierarchy record.
5. Preview a CSV import with `email,full_name`.
6. Commit the CSV import and confirm the new member appears in settings.
7. Generate a students CSV export.
8. Update branding and policy settings.
9. Confirm a student account cannot PATCH branding or policies.

## Enterprise Platform Pass 2

Scoped enterprise roles:

- `report_viewer` can view enterprise dashboards, analytics, import templates, and export history.
- `export_manager` can create exports and view reports, but cannot modify policies, branding, members, departments, teams, or cohorts.
- `department_manager` can manage only departments where their organization membership is assigned as `manager` or `admin`.
- `team_manager` can manage only assigned teams.
- `cohort_manager` can manage only assigned cohorts.
- Company, university, platform, and super admins keep broad organization management capability.

Branding uploads:

- Branding keeps URL compatibility through `logo_url`, `banner_url`, and `favicon_url`.
- Storage-backed assets are supported for `logo`, `banner`, `favicon`, `certificate_logo`, and `email_header_image`.
- Upload endpoint: `POST /api/v1/organizations/{organization_id}/enterprise/branding/upload/`.
- Accepted image MIME types: PNG, JPEG, WEBP, ICO.
- Accepted extensions: `.png`, `.jpg`, `.jpeg`, `.webp`, `.ico`.
- Maximum branding asset size is 5 MB.
- Assets are treated as public branding assets. Do not upload private or confidential files.

Async export lifecycle:

- `DataExportJob.status` values are `queued`, `processing`, `completed`, `failed`, and `cancelled`.
- Export creation queues a job through `POST /api/v1/organizations/{organization_id}/enterprise/exports/`.
- Export files are generated by:

```powershell
python manage.py process_data_exports --limit 50
```

- Supported formats are CSV and XLSX.
- Supported export types are `students`, `recruiters`, `applications`, `certificates`, `courses`, `audit_logs`, and `analytics_summary`.
- Audit log exports require `export_manager`, `platform_admin`, or `super_admin`.
- Completed files are available at `GET /api/v1/organizations/{organization_id}/enterprise/exports/{export_id}/download/`.
- Expired export cleanup is intentionally not automatic yet.

Analytics definitions:

- Student activation rate: course enrollments divided by active learners.
- Course completion rate: completed enrollments divided by total enrollments.
- Certificate completion rate: issued certificates divided by active learners.
- Placement rate: accepted offers divided by active learners.
- Applications and interviews are grouped by current status.
- Cohort progress is calculated from enrollments for members assigned to each cohort.
- Department and cohort breakdowns return member counts and status.
- Monthly trends currently summarize jobs, applications, and certificates created in the last 30 days.
- AI usage remains a placeholder until AI event billing and usage aggregation are finalized.

Bulk import templates:

- Template metadata endpoint: `GET /api/v1/organizations/{organization_id}/enterprise/imports/template/?import_type=students`.
- CSV template download: add `download=1`.
- Supported templates: students, recruiters, instructors, employees, departments, teams, cohorts, skills, course assignments, and cohort assignments.
- Import jobs store required columns, validation errors, an error report, and partial success summary.
- Course assignment and skills imports are template/validation-ready but not fully materialized into domain records yet.

Enterprise Pass 2 manual testing:

1. Sign in as a company admin and upload a PNG logo from `/organization/branding`.
2. Open `/organization/import`, choose `cohorts`, show the template, and download the CSV template.
3. Preview and commit a cohort import.
4. Queue a students CSV export and run `python manage.py process_data_exports --limit 50`.
5. Refresh `/organization/export` and download the completed export.
6. Queue an XLSX export and confirm the generated file downloads.
7. Create a `report_viewer` organization membership and confirm dashboard access but policy update denial.
8. Create an `export_manager` membership and confirm export creation but policy update denial.
9. Assign a `department_manager` as manager on one department and confirm they can update only that department.

## Enterprise Platform Pass 3

Worker automation:

- Organization exports, imports, reports, and scheduled maintenance hooks now use shared service lifecycle methods.
- Celery tasks are available in `apps.organizations.tasks`:
  - `apps.organizations.process_data_export`
  - `apps.organizations.process_bulk_import`
  - `apps.organizations.process_enterprise_report`
  - `apps.organizations.expire_data_exports`
- API views queue work through Celery and fall back to synchronous processing if Celery dispatch is unavailable in local/test environments.
- Operational fallback command:

```powershell
python manage.py process_data_exports --limit 50
python manage.py process_data_exports --limit 50 --reports
python manage.py process_data_exports --expire
```

Lifecycle fields:

- Import/export/report jobs track `queued`, `validating`, `processing`, `completed`, `failed`, and `cancelled` style states.
- Jobs track progress percentage, start time, completion time, duration, retry count, failure reason, actor, and organization.
- Transitions are audit logged.

Export lifecycle:

- Exports track `retention_days`, `expires_at`, `download_count`, `last_downloaded_at`, and `deleted_at`.
- Completed exports become `expired` through scheduled cleanup; files are not silently removed.
- Manual delete marks the export cancelled/deleted and writes audit history.
- Download endpoint increments download counters.

Bulk import engine:

- Imports track validation rows, error report, required columns, partial success report, duplicate summary, and progress.
- Supported templates: students, recruiters, instructors, employees, departments, teams, cohorts, skills, course assignments, and cohort assignments.
- Skills and course assignments are accepted as lifecycle-ready rows; deep domain materialization remains future work.

Enterprise role management:

- `/organization/roles` provides search, role assignment, and permission summary.
- API: `GET/POST /api/v1/organizations/{organization_id}/enterprise/roles/`.
- Role changes use the existing membership role change service and audit log path.

Audit center:

- `/organization/audit` supports search and action filtering.
- API: `GET /api/v1/organizations/{organization_id}/enterprise/audit/`.
- CSV/XLSX style export is available through `file_format`.
- Response shape is `{ total, events }` to avoid pagination-envelope ambiguity.

Enterprise reports:

- `/organization/reports` queues and monitors asynchronous enterprise reports.
- API: `GET/POST /api/v1/organizations/{organization_id}/enterprise/reports/`.
- Reports currently generate downloadable analytics summary XLSX exports.
- Report types include enrollment, placement, hiring, recruiter activity, certificate completion, course completion, department summary, cohort summary, organization summary, and engagement summary.

Organization lifecycle:

- API: `POST /api/v1/organizations/{organization_id}/enterprise/lifecycle/`.
- Supported actions: suspend, reactivate, archive, soft delete, transfer ownership.
- Active organizations with active members cannot be archived directly; suspend first.
- Active organizations cannot be soft deleted.
- Lifecycle changes are audit logged and keep metadata.

Enterprise Pass 3 manual testing:

1. Open `/organization/roles`, search members, and assign `report_viewer` or `export_manager`.
2. Confirm `report_viewer` can open dashboard/audit but cannot update policies.
3. Open `/organization/audit`, filter by `organization_export`, and confirm events render.
4. Open `/organization/reports`, queue an organization summary report, and confirm progress/completion.
5. Run `python manage.py process_data_exports --reports --limit 50` if Celery is not running.
6. Download the report export.
7. Queue a CSV export, download it twice, and confirm download count changes in API/admin.
8. Run `python manage.py process_data_exports --expire` after setting an export `expires_at` in the past.
9. Suspend and reactivate an organization from `/organization/settings`.

## Enterprise Reporting and Import Completion Pass

Report datasets:

- Enterprise reports now generate report-specific export rows rather than a single analytics summary placeholder.
- Supported report export types:
  - `enrollment_report`
  - `placement_report`
  - `hiring_report`
  - `recruiter_activity_report`
  - `certificate_completion_report`
  - `course_completion_report`
  - `department_summary_report`
  - `cohort_summary_report`
  - `organization_summary_report`
  - `engagement_summary_report`
  - `export_summary_report`
- Legacy report type values such as `organization_summary` remain accepted and map to the new report export types.
- Reports support CSV and XLSX through the same storage-backed export infrastructure.
- Report generation is organization-scoped and uses enterprise export permissions.

Import materialization:

- Bulk imports now persist data for members, departments, teams, cohorts, skills, courses, course assignments, and cohort assignments.
- Member imports can attach rows to departments, teams, and cohorts when optional columns are supplied.
- Skills create or update portfolio skills for active organization members.
- Course imports create or update courses for instructors who are members of the organization.
- Course assignment imports create enrollments and can optionally assign the learner to a cohort.
- Import jobs track created, updated, skipped, failed, duplicate, and success counts.
- Row-level failures are stored in `error_report`; summary counts are stored in `partial_success_report`.

Import files:

- Import jobs generate CSV summary files and CSV error files.
- API: `GET /api/v1/organizations/{organization_id}/enterprise/imports/{import_id}/summary/download/`.
- API: `GET /api/v1/organizations/{organization_id}/enterprise/imports/{import_id}/errors/download/`.
- Download endpoints require organization-scoped access and audit each download.

Audit center filters:

- Audit center supports action contains, action prefix, severity metadata, actor, target type, target id, date range, and free-text search.
- CSV and XLSX audit exports respect the same organization scope and filters.

Worker verification:

- Enterprise worker status records track heartbeat, last success, last failure, average duration, failure count, retry count, stuck-job count, and metadata.
- `/organization/reports` displays worker status cards from `GET /api/v1/organizations/{organization_id}/enterprise/worker-jobs/`.
- Stuck jobs are detected when processing jobs have not updated for more than one hour.

Export retention cleanup:

- Exports support `retention_days`, `expires_at`, `legal_hold`, and `file_deleted_at`.
- `python manage.py process_data_exports --expire` marks expired completed exports.
- `python manage.py process_data_exports --expire --delete-expired-files` deletes files only when explicitly requested.
- Exports with legal hold are skipped and audited.
- Files are not deleted by default.

Tenant isolation regression coverage:

- Tests prove cross-organization report access is denied.
- Tests prove cross-organization export and import-file downloads are denied.
- Tests prove report viewers and export managers cannot mutate restricted data.
- Tests prove audit export/filtering remains organization-scoped.

Enterprise completion manual testing:

1. Open `/organization/reports`, queue `enrollment_report` as CSV and XLSX, then download the result.
2. Queue `export_summary_report` and confirm export lifecycle metadata appears in the file.
3. Open `/organization/import`, import students, skills, courses, and course assignments.
4. Download import summary and error CSV files from the import result panel.
5. Open `/organization/audit`, filter by action prefix and severity.
6. Open `/organization/export`, generate a report export and confirm download count increments after download.
7. Run `python manage.py process_data_exports --expire` and confirm expired records are marked but files remain.
8. Set legal hold on an export in admin and confirm cleanup skips it.
9. Run a staging Celery worker and confirm worker heartbeat/status appears on `/organization/reports`.

## AI Platform Pass 1

AI architecture:

- `apps.ai_platform` is the central AI infrastructure layer.
- Application features must call `AIService`; provider SDKs live only behind `apps.ai_platform.providers`.
- Existing tutor APIs remain compatible, but tutor generation now routes through `AIService`.
- The platform currently defaults to a mock provider so local development and tests never require real provider keys.

AI data model:

- `AIProvider` stores provider identity, type, active/default flags, retry and timeout configuration.
- `AIModelConfiguration` stores provider models, token limits, temperature, and cost metadata.
- `AIPromptTemplate` stores reusable prompts with versioning, locale, variables, and variant fields for A/B testing.
- `AIConversation` stores user-facing conversation metadata.
- `AIRequest` and `AIResponse` store gateway calls and outputs.
- `AITokenUsage` and `AIUsage` track token usage, request counts, estimated cost, latency, provider, model, feature, user, organization, and course.
- `AIBudgetPolicy` supports daily/monthly request, token, and cost limits by global, organization, user, or feature scope.
- `AIJob` and `AIResult` provide the queued long-running job foundation.

Provider framework:

- Provider types: `openai`, `anthropic`, `google_gemini`, `azure_openai`, `local`, and `mock`.
- `MockAIProvider` is safe for tests and local development.
- `OpenAIProvider` is isolated behind the provider interface and requires `OPENAI_API_KEY`.
- Other provider types are placeholder providers until their SDK verification and signing/cost policies are implemented.

AI gateway:

- Primary gateway method: `AIService.generate_text()`.
- Streaming-ready method: `AIService.stream_text()`.
- Feature helpers: `summarize`, `extract_skills`, `score_resume`, `analyze_portfolio`, and `generate_feedback`.
- API endpoints expose foundations for chat, resume review, portfolio review, career advice, learning recommendations, and job matching.

Prompt system:

- Prompt templates support `key`, `feature`, `version`, `locale`, `variant`, `system_prompt`, `user_prompt`, and variable lists.
- Default templates are seeded lazily by `AIService.ensure_defaults()`.
- Rendering uses Django template variables and stores the rendered prompt on `AIRequest`.

Budgeting and analytics:

- Budget enforcement runs before provider calls.
- Usage is aggregated daily by user, organization, course, feature, provider, and model.
- Admin analytics include request count, success rate, failure rate, average latency, feature usage, provider usage, total tokens, and estimated cost.

Safety foundation:

- Prompt validation detects common prompt-injection markers and overlong prompts.
- Redaction hooks mask secret-like terms in stored request input.
- AI endpoints use scoped DRF throttling through `AIRateThrottle`.
- Provider fallback currently falls back to a configured mock provider when a primary provider fails.
- Audit logs record AI request success/failure and queued jobs.

AI APIs:

- `GET /api/v1/ai/`
- `POST /api/v1/ai/chat/`
- `POST /api/v1/ai/resume-review/`
- `POST /api/v1/ai/portfolio-review/`
- `POST /api/v1/ai/career-advice/`
- `POST /api/v1/ai/learning-recommendations/`
- `POST /api/v1/ai/job-matching/`
- `GET /api/v1/ai/history/`
- `GET /api/v1/ai/conversations/`
- `GET/POST /api/v1/ai/jobs/`
- `GET /api/v1/ai/settings/`
- `GET /api/v1/ai/admin/`

Frontend:

- `/ai` provides a reusable AI chat/workbench surface.
- `/ai/history` lists recent AI requests.
- `/ai/settings` shows active providers and models.
- `/ai/admin` shows platform-admin AI analytics, prompts, usage, and cost summaries.

Manual testing:

1. Open `/ai`, submit a chat prompt, and confirm a mock response with token/latency/cost metadata.
2. Open `/ai/history` and confirm the request appears.
3. Open `/ai/settings` and confirm the mock provider/model is listed.
4. Log in as a platform admin and open `/ai/admin`.
5. Create an `AIBudgetPolicy` with a zero daily limit in Django admin and confirm requests are blocked.
6. Configure a non-mock provider only in staging after provider keys, cost policy, timeout, and safety review are complete.

AI environment variables:

- `OPENAI_API_KEY`
- `AI_DEFAULT_PROVIDER`
- `AI_ENABLE_REAL_PROVIDERS`
- `AI_REQUEST_TIMEOUT_SECONDS`
- `THROTTLE_AI_RATE`

## AI Platform Pass 2

Provider architecture:

- Providers still implement the shared `BaseAIProvider` interface.
- Supported adapters:
  - `MockAIProvider`
  - `OpenAIProvider`
  - `AnthropicProvider`
  - `GeminiProvider`
  - `AzureOpenAIProvider`
  - `LocalProvider` for Ollama/OpenAI-compatible local endpoints
- Provider SDK and HTTP calls remain isolated in `apps.ai_platform.providers`.
- Provider configuration supports metadata, timeouts, retry limits, health status, last check time, and last error.
- Environment variables:
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY`
  - `GEMINI_API_KEY`
  - `AZURE_OPENAI_API_KEY`
  - `AZURE_OPENAI_ENDPOINT`

Streaming:

- `AIService.stream_text()` creates an `AIRequest`, streams provider chunks, persists the final `AIResponse`, tracks usage, and emits completion metadata.
- `POST /api/v1/ai/chat/` accepts `stream=true` and returns Server-Sent Events.
- Stream events include `token`, `done`, `error`, and `cancelled`.
- `POST /api/v1/ai/requests/{request_id}/cancel/` marks a request cancelled.
- `/ai` uses streaming and exposes a cancel action.

Moderation:

- `AIModerationService` provides provider-neutral input/output moderation.
- Moderation tracks harm markers, unsafe content markers, prompt injection findings, PII findings, severity, categories, provider, and raw result metadata.
- Blocked moderation actions write audit events.
- API: `POST /api/v1/ai/moderation/`.

Privacy and redaction:

- `AIPrivacyService` redacts email addresses, phone numbers, government ID-like strings, addresses, and custom sensitive fields.
- Redacted input is stored on `AIRequest`.
- Vector documents store both original content and redacted content; retrieval returns redacted content.
- Future policy expansion should move custom sensitive fields into dedicated organization AI policies.

Vector search foundation:

- `VectorCollection` stores collection metadata, organization scope, embedding model, and dimensions.
- `VectorDocument` stores document type, object id, title, content, redacted content, deterministic local embedding, and metadata.
- Supported document types are open-ended and intended for courses, lessons, certificates, resumes, portfolios, skills, and jobs.
- `AIVectorService.index_document()` handles redaction and embedding.
- `AIVectorService.search()` provides semantic search using cosine similarity.
- APIs:
  - `POST /api/v1/ai/vectors/index/`
  - `POST /api/v1/ai/vectors/search/`

Evaluation framework:

- `AIEvaluationDataset` stores golden examples by feature.
- `AIEvaluationRun` stores provider/model/template comparison runs.
- `AIEvaluationResult` stores input, expected output, actual output, score, latency, estimated cost, hallucination notes, and manual score foundation.
- API:
  - `GET/POST /api/v1/ai/evaluations/`
  - `POST /api/v1/ai/evaluations/run/`

Budget and cost reconciliation:

- Token usage now stores provider-reported tokens, actual cost, and cost variance.
- `AIService.reconcile_costs()` updates provider-reported usage and actual cost for a request.
- Budget policies support alert thresholds and last alert timestamps.
- API:
  - `GET/POST /api/v1/ai/costs/`

Feature flags:

- `AIFeatureFlag` supports global, organization, and user overrides for AI features.
- Feature checks run before generation and streaming.
- API:
  - `GET/POST /api/v1/ai/feature-flags/`

Admin console:

- `/ai/admin` now displays provider status, prompt templates, feature flags, evaluation runs, and cost summary cards.
- `GET /api/v1/ai/providers/status/` returns provider health and comparison data.

Manual testing:

1. Open `/ai`, submit a prompt, watch the response stream, then try cancel.
2. Open `/ai/admin` as a platform admin and verify provider status, feature flags, evaluation summary, and cost cards.
3. Use Django admin to disable `chat` with an `AIFeatureFlag`, then confirm `/ai` blocks chat.
4. POST to `/api/v1/ai/vectors/index/`, then `/api/v1/ai/vectors/search/`, and confirm redacted search results.
5. Create an evaluation dataset and run it through `/api/v1/ai/evaluations/run/`.
6. Reconcile a request cost through `POST /api/v1/ai/costs/`.

Known AI Pass 2 limitations:

- Provider integrations are adapter-ready, but only OpenAI uses an installed SDK path; Anthropic, Gemini, Azure, and local providers use HTTP adapter foundations.
- The local vector store uses JSON embeddings and cosine similarity; it is suitable for foundation tests, not large-scale RAG.
- Moderation is local-rule based until provider moderation adapters are configured.
- Streaming cancellation is cooperative and request-state based.

## AI Product Pass 1: Resume Intelligence

AI Resume Intelligence is the first product feature built on top of the centralized AI Platform. It lives in the careers domain and calls `AIService` for every generation, moderation, budget, feature-flag, usage, and audit path.

Architecture:

- `ResumeAIReview` stores review history for `CareerResume`.
- Each review links back to the `AIRequest` and `AIResponse` created by `AIService`.
- Raw provider output is stored only in AI platform records; recruiter-facing summaries use a restricted serializer.
- Prompt version is tracked with `prompt_version="resume-intelligence-v1"`.
- Estimated cost, model name, confidence, section scores, ATS score, match score, extracted skills, strengths, weaknesses, suggestions, and prioritized actions are stored per review.

APIs:

- `POST /api/v1/careers/resumes/{resume_id}/ai/review/`
- `POST /api/v1/careers/resumes/{resume_id}/ai/review/stream/`
- `POST /api/v1/careers/resumes/{resume_id}/ai/skills/`
- `POST /api/v1/careers/resumes/{resume_id}/ai/ats/`
- `POST /api/v1/careers/resumes/{resume_id}/ai/job-match/`
- `POST /api/v1/careers/resumes/{resume_id}/ai/compare/`
- `GET /api/v1/careers/resumes/{resume_id}/ai/history/`
- `GET /api/v1/careers/resumes/{resume_id}/ai/analytics/`
- `GET /api/v1/careers/resumes/{resume_id}/ai/recruiter-summary/?organization_id=...`

Scoring methodology:

- Overall score is computed from section-level deterministic signals: ATS friendliness, grammar, professional tone, formatting, keyword coverage, action verbs, achievements, education, experience, skills, projects, certifications, and length.
- The AI model provides narrative support through `AIService`; deterministic scoring keeps score history stable and testable.
- Strengths and weaknesses are derived from high and low section scores.
- Suggestions and action items are prioritized from weak sections and missing job keywords.

ATS methodology:

- ATS compatibility uses resume structure, target role, skills, experience count, education presence, keyword coverage, and formatting signals.
- ATS reports include compatibility score, missing keywords, formatting issues, duplicate content placeholder, weak summaries, weak bullets, and unreadable sections.
- This is an estimation, not a guarantee of behavior in any specific applicant tracking system.

Skill normalization:

- Skills are extracted into technical skills, soft skills, languages, tools, frameworks, platforms, cloud providers, databases, and certificates.
- Extracted skills are normalized against the platform skill catalog using `PortfolioSkill` names.
- Reviews store catalog matches and uncataloged skills to support future catalog governance.

Job matching:

- Job matching compares selected resume skills against `JobListing.required_skills` and `preferred_skills`.
- Reports include match score, missing skills, matched skills, keyword overlap, experience fit, education fit, confidence, explanation, and recommendations.

Version comparison:

- Comparison reviews compare two owned resumes.
- Reports include added skills, removed skills, ATS improvement estimate, score change, and wording improvement signal.

Analytics:

- Resume AI analytics expose average score, best score, review count, top weaknesses, top strengths, score history, skill growth, ATS trend, and job match trend.
- `/resumes/{resumeId}` now shows AI review actions, latest score cards, top actions, AI history, and AI review analytics.

Privacy considerations:

- Resume AI endpoints require the resume owner, except recruiter summary access.
- Recruiter summary requires `CandidateVisibilityService.can_view_resume()`.
- Recruiter summary does not expose internal prompts, raw provider output, full report payload, or AI request metadata.
- Resume text passes through `AIService`, which applies feature flags, budget enforcement, privacy redaction, moderation, usage tracking, and audit logging.
- The moderation false-positive for `skills` matching the harm term `kill` was fixed by matching safety terms on word boundaries.

Manual testing:

1. Sign in as a student and open `/resumes`.
2. Open a resume detail page and click `Review`, `ATS`, and `Extract skills`.
3. Copy a public job id into `Job ID for match` and run job match.
4. Copy another owned resume id into `Resume ID to compare` and run comparison.
5. Confirm AI history and analytics update after each run.
6. Sign in as a recruiter with candidate unlock and organization entitlement, then call the recruiter summary endpoint and confirm only summary fields are returned.

## AI Product Pass 2: Portfolio Intelligence

AI Portfolio Intelligence extends the same AI Platform contract to portfolios and projects. All generation routes call `AIService`, so provider abstraction, moderation, privacy redaction, feature flags, budget enforcement, usage tracking, AI analytics, and audit records remain centralized.

Architecture:

- `PortfolioAIReview` stores portfolio review history, project reviews, GitHub checks, skill extraction runs, and job-match reports.
- Each review links to the owning `Portfolio`, optional `PortfolioProject`, optional `JobListing`, and the `AIRequest`/`AIResponse` generated by `AIService`.
- Prompt version is tracked with `prompt_version="portfolio-intelligence-v1"`.
- Reviews store scores, confidence, extracted skills, missing skills, technology stack, strengths, weaknesses, suggestions, action items, model name, and estimated cost.
- Recruiter-facing AI summaries use a restricted serializer and never expose prompts, raw model output, provider payloads, or internal reasoning.

APIs:

- `POST /api/v1/careers/portfolio/me/ai/review/`
- `POST /api/v1/careers/portfolio/me/ai/review/stream/`
- `POST /api/v1/careers/portfolio/me/ai/project-review/`
- `POST /api/v1/careers/portfolio/me/ai/github/`
- `POST /api/v1/careers/portfolio/me/ai/skills/`
- `POST /api/v1/careers/portfolio/me/ai/job-match/`
- `GET /api/v1/careers/portfolio/me/ai/history/`
- `GET /api/v1/careers/portfolio/me/ai/analytics/`
- `GET /api/v1/careers/portfolio/{username}/ai/recruiter-summary/?organization_id=...`

Portfolio scoring:

- Overall portfolio score combines profile completeness, bio, skills, project count, project quality, presentation quality, professionalism, and consistency.
- Project quality evaluates architecture, technology choices, code organization, innovation, complexity, business relevance, scalability, testing, deployment readiness, documentation, and portfolio presentation.
- Deterministic scoring keeps analytics stable while the model provides narrative feedback through the centralized AI pipeline.

GitHub analysis:

- GitHub Intelligence is provider-ready but does not fetch repository contents yet.
- Current scoring uses available GitHub profile and repository URLs, then reports repository details as `unknown_without_provider_fetch`.
- If no GitHub URL exists, the review skips gracefully and recommends adding repository links, README evidence, tests, CI/CD, and license details.

Skill extraction and job matching:

- Skills are extracted from portfolio text, project technology stacks, and existing portfolio skills.
- Extracted skills are normalized against current `PortfolioSkill` catalog names as a foundation for a future global skills catalog.
- Portfolio job match compares normalized portfolio skills to job required and preferred skills, then reports match score, missing skills, project relevance, technology overlap, confidence, explanation, and suggested next projects.

Analytics:

- Portfolio AI analytics expose average score, best score, review count, top strengths, top weaknesses, score history, project quality trend, skill growth, technology diversity, and job match trend.
- `/career-profile` shows AI review actions, project review, GitHub analysis, skill extraction, job match, latest summary, next actions, growth timeline, and AI analytics cards.

Privacy and recruiter access:

- Student AI endpoints require authentication and operate on the signed-in user's portfolio.
- Recruiter summary requires `CandidateVisibilityService.can_view_portfolio()` with organization context.
- Recruiters see a concise quality summary, technology stack, strengths, confidence, and growth signals only.

Budgeting:

- Portfolio review and GitHub/project analysis use the `portfolio_review` AI feature.
- Skill extraction uses the `skill_gap_analysis` feature.
- Portfolio job matching uses the `job_matching` feature.
- Feature flags and usage budgets are enforced by `AIService` before a review record is created.

Manual testing:

1. Sign in as a student and open `/career-profile`.
2. Add at least one project with technologies and optional GitHub/demo links.
3. Click `AI Review`, `GitHub analysis`, and `Extract skills`.
4. Select a project and run `Run project review`.
5. Paste a job id and run `Run job match`.
6. Confirm the latest score cards, action list, history, and analytics update.
7. Sign in as an entitled recruiter with candidate visibility and call the recruiter summary endpoint; confirm only safe summary fields are returned.

Known Portfolio Intelligence limitations:

- GitHub repository contents are not fetched yet; repository quality is estimated from links and portfolio metadata.
- Public portfolio pages do not display AI outputs by default to avoid exposing private scoring without explicit privacy controls.
- Streaming is exposed as an API endpoint; the first frontend panel uses non-streaming actions with clear loading states.
- Scoring is useful for prioritization, not a guarantee of recruiter preference or hiring outcome.

## AI Product Pass 3: Interview Coach

AI Interview Coach turns the centralized AI Platform into a mock interview product. All generation and evaluation calls route through `AIService`, so provider abstraction, moderation, privacy redaction, feature flags, budget enforcement, usage tracking, audit logging, and AI analytics stay centralized.

Architecture:

- `AIInterviewSession` stores session type, difficulty, status, organization, role context, skills, history, trends, provider/model, token usage, cost, summary, and final feedback.
- `AIInterviewQuestion` stores generated questions, follow-up links, sequence, skill area, and links to the `AIRequest`/`AIResponse`.
- `AIInterviewAnswerEvaluation` stores student answers, scoring dimensions, strengths, weaknesses, better-answer guidance, tips, and next practice goal.
- `AIInterviewTemplate` lets authorized organization users create reusable recruiter interview packs without exposing prompts.
- `SpeechToTextProvider`, `TextToSpeechProvider`, and `MockVoiceProvider` define a provider-neutral voice foundation for later speech integrations.

APIs:

- `POST /api/v1/ai/interview/sessions/`
- `GET /api/v1/ai/interview/sessions/`
- `GET /api/v1/ai/interview/sessions/{session_id}/`
- `POST /api/v1/ai/interview/sessions/{session_id}/next-question/`
- `POST /api/v1/ai/interview/sessions/{session_id}/submit-answer/`
- `POST /api/v1/ai/interview/sessions/{session_id}/evaluate-answer/`
- `POST /api/v1/ai/interview/sessions/{session_id}/pause/`
- `POST /api/v1/ai/interview/sessions/{session_id}/resume/`
- `POST /api/v1/ai/interview/sessions/{session_id}/cancel/`
- `POST /api/v1/ai/interview/sessions/{session_id}/finish/`
- `GET /api/v1/ai/interview/analytics/`
- `GET/POST /api/v1/ai/interview/templates/`

Session lifecycle:

- Students start an interview with type, difficulty, target role, industry, experience level, skills, language, resume context, and portfolio context.
- The next-question endpoint asks `AIService` for one non-repeating question and stores the linked request/response.
- The submit-answer endpoint sends the question and answer through `AIService`, then persists normalized scores and coaching guidance.
- Finish generates a final report with question reviews, score, trends, improvement roadmap, recommended learning, duration, cost, and timeline history.
- Pause, resume, and cancel actions update the session timeline and audit trail.

Evaluation methodology:

- Each answer is scored across clarity, confidence, technical quality, communication, structure, problem solving, accuracy, and professionalism.
- Deterministic score normalization keeps analytics stable, while AI output supplies narrative feedback and better-answer guidance.
- Scores are coaching signals only; they are not hiring decisions and should not be used as automated candidate rejection criteria.

Recruiter mode:

- Organization templates are permission controlled.
- Organization managers and platform admins can create templates.
- Organization members can list active templates for their organization.
- Recruiters can view permission-controlled session summaries when they have organization access, but prompts and raw provider payloads are not exposed.

Analytics:

- User analytics include session count, completed count, average score, average duration, practice frequency, weak areas, strong areas, AI cost, and organization usage.
- AI platform usage records still track `interview_coach` requests by user, organization, provider, model, tokens, latency, and estimated cost.

Privacy and safety:

- Interview prompts and answers pass through `AIService`, which performs privacy redaction and moderation before provider calls.
- Cross-user session access is denied unless the requester is platform admin or has organization-level access.
- Provider outputs are moderated before completion.
- Feature flags can disable `interview_coach` globally, per organization, or per user.
- Budget policies can limit interview coaching usage by user, organization, feature, or global scope.

Frontend:

- `/ai/interview` starts sessions and shows analytics, coaching focus, and recent sessions.
- `/ai/interview/history` lists previous mock interviews.
- `/ai/interview/session/{id}` supports next question, answer submission, pause, resume, cancel, finish, latest feedback, final report, and session replay.

Manual testing:

1. Sign in as a student and open `/ai/interview`.
2. Select `technical`, choose a difficulty, enter a role and skills, then start a session.
3. Generate a question, submit an answer, and confirm the score and coaching tips appear.
4. Pause and resume the session.
5. Finish the session and confirm the final report, timeline, trends, token usage, and cost fields update.
6. Open `/ai/interview/history` and verify the completed session appears.
7. Disable the `interview_coach` feature flag for the user and confirm question generation is blocked.

Known Interview Coach limitations:

- Voice is provider-ready but remains mock-only.
- Streaming support is API-ready for generated questions; the first frontend uses normal request/response loading states.
- Evaluation scoring is coaching-oriented and must not be used as an automated employment decision.
- Organization template UI is API-ready but not yet exposed as a dedicated recruiter screen.

## AI Quality & Safety Platform Pass

This pass extends the centralized AI Platform rather than adding another AI product. The same quality, safety, privacy, feedback, cache, and monitoring foundations apply to Resume Intelligence, Portfolio Intelligence, Interview Coach, and future AI products.

Evaluation methodology:

- `AIEvaluationDataset` now supports dataset type, golden dataset flag, expected schema, versioning, examples, and feature ownership.
- `AIEvaluationRun` stores average score, confidence score, latency, cost, prompt version, and structured report metadata.
- `AIEvaluationResult` stores score breakdowns, confidence, hallucination notes, bias flags, privacy flags, prompt-security flags, and manual-review status.
- `AIEvaluationService.run_dataset()` records latency, cost, confidence, privacy, fairness, and prompt-security signals for every example.

Confidence and explainability:

- `AICalibrationReport` stores score name, score, confidence score, confidence level, evidence, score breakdown, weighting, uncertainty, missing information, limitations, and recommended next action.
- Explainability reports expose user-safe evidence and summaries only.
- Internal prompts, provider payloads, and chain-of-thought are not exposed.

Bias and fairness:

- `AIFairnessReport` records fairness score, bias flags, manual-review requirement, organization context, and report metadata.
- The foundation checks gender, country, accent, education, experience, language, cultural, and age bias marker classes.
- AI outputs must not automatically reject or rank candidates.

Prompt security:

- `AISafetyService` now detects direct prompt injection, template injection, unsafe HTML, malicious URLs, markdown/script vectors, and tool-abuse style phrases.
- Unsafe prompts can be blocked before provider calls.
- Prompt input is escaped before prompt rendering.

Privacy and DLP:

- `AIPrivacyService` detects and redacts email, phone, address, passport, national/student IDs, bank accounts, credit cards, government IDs, organization secrets, and API keys.
- `AIPrivacyReport` stores findings, redaction count, feature, organization, severity, and applied policy.
- Privacy redactions create audit events.

Feedback loop:

- `AIFeedback` stores helpful/not helpful/incorrect/hallucination/unsafe/biased/incomplete feedback with feature, provider, model, prompt version, organization, and user context.
- Feedback is included in quality dashboard summaries for future evaluation tuning.

Cost optimization:

- `AIResponseCache` stores duplicate response cache entries by feature, organization, model, and redacted input hash.
- `AIService.generate_text()` checks the cache after moderation/redaction and before provider execution unless disabled by metadata.
- Cache hits create AI request records with cache metadata but no provider token cost.

Monitoring and dashboards:

- `/api/v1/ai/quality/` returns request counts, failure/block rates, cost, tokens, latency, evaluation history, feature quality, bias reports, privacy reports, feedback, provider comparison, cache stats, and confidence trends.
- `/ai/quality` displays the quality dashboard in the browser.
- `/api/v1/ai/providers/comparison/` and `/api/v1/ai/cache/statistics/` are platform-admin endpoints.

New APIs:

- `GET /api/v1/ai/quality/`
- `GET /api/v1/ai/providers/comparison/`
- `GET /api/v1/ai/cache/statistics/`
- `GET/POST /api/v1/ai/feedback/`
- `POST /api/v1/ai/bias/report/`
- `POST /api/v1/ai/privacy/report/`
- `POST /api/v1/ai/confidence/explain/`

Manual testing:

1. Sign in and open `/ai/quality`.
2. Run a resume, portfolio, or interview AI request.
3. Confirm request count, provider comparison, privacy reports, and cache stats update.
4. Submit feedback through `POST /api/v1/ai/feedback/`.
5. Run `POST /api/v1/ai/privacy/report/` with sample PII and confirm redactions.
6. Run `POST /api/v1/ai/bias/report/` with biased text and confirm manual review is required.
7. Run an evaluation dataset and confirm evaluation history appears on `/ai/quality`.

Known AI quality limitations:

- Fairness detection is marker-based foundation logic, not a full bias classifier.
- Hallucination detection is stored and report-ready but does not yet use retrieval-backed factuality checks.
- Response caching is conservative but still needs product-level invalidation policies for rapidly changing context.
- `/ai/admin` still needs richer visual panels for all quality signals; `/ai/quality` is the first dedicated screen.

## AI Evaluation Operations Pass

This pass turns AI quality from passive reporting into an operating process for model, prompt, safety, privacy, and governance review. It does not add new AI user products.

Scheduled-ready evaluation runs:

- `python manage.py run_ai_evaluations` runs active evaluation datasets through `AIService`.
- Supported filters: `--dataset-type`, `--feature`, `--provider`, `--prompt-version`, `--limit`, and `--dry-run`.
- `AIEvaluationRun` now records status, start time, completion time, duration, failure reason, aggregate results, latency, cost, score, confidence, provider, and model.
- Evaluation requests disable response cache so quality checks measure the current model/prompt path.

Dataset management:

- Dataset types include resume intelligence, portfolio intelligence, interview coach, career coach, learning tutor, job matching, skill extraction, prompt security, privacy/DLP, fairness, hallucination, and legacy golden datasets.
- Datasets store expected score range, rubric, risk tags, locale, difficulty, status, reviewer notes, golden input examples, and expected output.
- Draft, active, inactive, and archived dataset statuses let teams stage datasets before production use.

Human reviewer workflow:

- `AIEvaluationReview` supports assignment, approval, rejection, manual scores, notes, hallucination flags, bias flags, unsafe flags, and prompt revision requests.
- Reviewer identity and timestamps are stored.
- Reviewer actions create audit events.

Red-team testing:

- `AIRedTeamSuite` and `AIRedTeamResult` support prompt injection, jailbreak, malicious resume, malicious portfolio, malicious interview answer, unsafe URL, hidden instruction, RAG poisoning, and PII leakage cases.
- Red-team runs route through the same moderation, privacy, provider, budget, and usage path as other AI work.
- Results store detected flags, pass/fail state, severity, mitigation notes, output excerpt, provider, and model.

Prompt and model comparison:

- `AIComparisonReport` compares provider, model, prompt version, or feature version labels for a selected feature.
- Reports aggregate quality, safety, privacy, latency, cost, token usage, failure rate, and winner metadata from stored evaluation runs.

AI audit exports:

- `AIAuditExport` supports CSV and XLSX exports for evaluation runs, safety events, privacy events, bias events, feedback, provider usage, prompt versions, and model comparisons.
- Exports are platform-admin only.
- Export creation records audit events and stores generated files in configured storage.

New operations APIs:

- `POST /api/v1/ai/evaluations/run-filtered/`
- `GET /api/v1/ai/evaluations/reviewer-queue/`
- `PATCH /api/v1/ai/evaluations/results/{result_id}/review/`
- `GET /api/v1/ai/red-team/suites/`
- `POST /api/v1/ai/red-team/run/`
- `GET/POST /api/v1/ai/comparisons/`
- `GET/POST /api/v1/ai/audit-exports/`

Dashboard and admin screens:

- `/ai/quality` now shows reviewer queue counts, red-team health, comparison reports, audit exports, and evaluation history.
- `/ai/admin` now includes platform-admin controls for launching evaluation runs, creating provider comparisons, and exporting audit CSV files.

Manual testing:

1. Sign in as platform admin and open `/ai/admin`.
2. Click `Launch evaluations` and confirm a run is created.
3. Open `/ai/quality` and confirm evaluation history, reviewer queue, red-team, comparisons, and audit export cards load.
4. Run `python manage.py run_ai_evaluations --dry-run --limit 5` and confirm no runs are created.
5. Run `python manage.py run_ai_evaluations --dataset-type interview_coach --limit 1`.
6. Create an audit export through `POST /api/v1/ai/audit-exports/`.
7. Create or seed a red-team suite, run `POST /api/v1/ai/red-team/run/`, and review the stored result.

Public AI launch checklist:

- Confirm active datasets exist for every public AI feature.
- Require reviewer coverage for high-risk features before public launch.
- Run prompt-security, privacy/DLP, fairness, hallucination, and red-team suites before every provider/model/prompt change.
- Export and archive evaluation evidence before release sign-off.
- Monitor cost, latency, cache hit ratio, failure rate, privacy flags, bias flags, and user feedback after launch.

Known AI evaluation operations limitations:

- Scheduling is command-ready, but no Celery beat schedule is enabled by default.
- Reviewer controls are API/admin-ready; the browser workflow is still intentionally lightweight.
- Red-team detection is foundation-level and must be expanded with stronger adversarial datasets.
- Comparison reports are aggregate summaries, not statistically rigorous A/B tests.
- Evaluation quality depends heavily on dataset coverage and reviewer discipline.

## AI Governance Release Pass

This pass adds controlled release management for AI prompts, models, providers, and feature flag rollouts. It does not add a new AI product.

Reviewer console:

- `/ai/reviewer` provides assigned reviews, unassigned reviews, filters, workload summary, per-review actions, and bulk approval.
- Reviewers can approve, reject, flag hallucination, flag bias, flag unsafe output, request prompt revision, and add reviewer notes.
- Platform admins can bulk assign reviews. Assigned reviewers can submit their own reviews.
- Reviewer APIs enforce AI reviewer permissions.

Release gates:

- `AIReleaseGate` tracks release status for prompt templates, model configuration changes, provider changes, and feature flag rollout changes.
- Supported statuses are draft, pending review, approved, rejected, promoted, and rolled back.
- Gates evaluate quality score, safety score, bias flags, privacy flags, hallucination flags, failure rate, latency, and estimated cost.
- A gate can be promoted only after approval.
- Rollbacks store rollback reason and timestamp.

Prompt/model change history:

- `AIChangeHistory` stores who changed a release item, previous version, new version, approval state, evaluation run used, promoted timestamp, rolled-back timestamp, and rollback reason.
- Gate creation, promotion, rollback, review assignment, review submission, red-team execution, and budget blocking create audit events.

Red-team dataset structure:

- Red-team suites support malicious resume, malicious portfolio, interview injection, hidden instructions, unsafe URL, RAG poisoning, PII leakage, bias trigger, and hallucination trap scenarios.
- Suites and cases support low, medium, high, and critical severity.
- Suites and cases store expected safe behavior so reviewers know what the AI should do.

Evaluation budgets:

- Filtered evaluation runs support max requests, max estimated cost, max tokens, and provider-specific request limits.
- Dry runs return budget estimates without creating runs.
- Hard budget violations block execution and write audit records.

Release dashboard:

- `/ai/admin` now shows release gate summary, pending approvals, failed gates, recent gates, rollback actions, eval budget dry run, red-team pass rate, and public AI launch checklist status.
- `/ai/quality` receives the same release governance summary through the quality dashboard API.

New governance APIs:

- `GET /api/v1/ai/evaluations/reviewer-queue/`
- `POST /api/v1/ai/evaluations/reviewer-queue/bulk-assign/`
- `POST /api/v1/ai/evaluations/reviewer-queue/bulk-approve/`
- `POST /api/v1/ai/evaluations/results/{result_id}/review/`
- `GET/POST /api/v1/ai/release-gates/`
- `POST /api/v1/ai/release-gates/{gate_id}/action/`
- `GET /api/v1/ai/release-gates/history/`
- `GET /api/v1/ai/launch-checklist/`

Public AI launch checklist:

- Minimum evaluation coverage
- Red-team pass rate
- DLP pass rate
- Bias review completed
- Prompt versions approved
- Model configurations approved
- Cost budget configured
- Reviewer sign-off completed
- Audit export ready

Manual testing:

1. Sign in as platform admin and open `/ai/admin`.
2. Click `Dry-run budget` and confirm request/token/cost estimate is shown.
3. Click `Launch evaluations` and confirm budget violations block unsafe runs.
4. Create a release gate from the latest evaluation run.
5. Promote an approved gate, then roll it back and confirm rollback history updates.
6. Open `/ai/reviewer` and filter by status, feature, dataset type, and risk tag.
7. Approve, reject, and flag a review from the reviewer console.
8. Run a red-team suite and confirm severity and expected safe behavior are stored.

Known AI governance limitations:

- Release gate thresholds are configurable but still simple rule checks.
- Reviewer console is functional but does not yet provide a full detail drilldown route per review.
- Red-team coverage depends on seeded datasets and should be expanded before public AI beta.
- Feature flag and prompt/model promotion records do not yet automatically mutate production config; they create governance approval records.
- Launch checklist readiness is advisory and must be paired with human release sign-off.

## AI Product Pass 4 - AI Career Coach

AI Career Coach is the long-term planning product built on top of the centralized AI Platform. Every generated assessment, roadmap, skill-gap report, recommendation, and weekly coaching summary routes through `AIService`, which means provider abstraction, moderation, privacy redaction, feature flags, budget enforcement, usage tracking, analytics, and audit logging remain centralized.

Architecture:

- `AICareerGoal` stores target role, target industry, target country, milestones, progress, completion state, and coaching history.
- `AICareerAssessment` stores readiness score, strengths, weaknesses, growth opportunities, recommendations, confidence, model metadata, request reference, and cost.
- `AICareerRoadmap` stores 3-month, 6-month, 12-month, and 24-month plans with milestones, recommended courses, projects, certifications, interview prep, resume improvements, portfolio improvements, networking, and job-search milestones.
- `AICareerSkillGap` stores target comparison, missing skills, priority skills, estimated learning time, recommended courses, recommended projects, confidence, and report metadata.
- `AICareerCoachingSummary` stores weekly progress, achievements, missed goals, recommended actions, upcoming priorities, motivation summary, confidence, and AI request reference.

Career Coach APIs:

- `GET/POST /api/v1/ai/career/goals/`
- `PATCH /api/v1/ai/career/goals/{goal_id}/`
- `POST /api/v1/ai/career/assessment/`
- `POST /api/v1/ai/career/roadmap/`
- `POST /api/v1/ai/career/skill-gap/`
- `POST /api/v1/ai/career/learning-recommendations/`
- `POST /api/v1/ai/career/weekly-coaching/`
- `GET /api/v1/ai/career/history/`
- `GET /api/v1/ai/career/analytics/`
- `GET /api/v1/ai/career/recruiter-summary/{candidate_id}/`

Frontend screens:

- `/ai/career` shows analytics, active goal, assessment, skill gap, weekly coaching, and recent history.
- `/ai/career/roadmap` generates and displays timeline-style roadmap milestones.
- `/ai/career/goals` creates and tracks career goals.
- `/ai/career/history` shows assessment and coaching history.

Skill gap methodology:

- The service compares profile skills from the user's portfolio/resume context with selected target skills, role, industry, company, country, or career goal.
- Missing skills are prioritized and paired with estimated learning windows, course recommendations, and project recommendations.
- Course recommendations use existing published course tags, descriptions, and learning outcomes where available.

Weekly coaching:

- Weekly summaries include progress, achievements, missed goals, actions, priorities, and motivation.
- Coaching history is linked back to career goals so long-term progress remains visible.

Analytics:

- Tracks active goals, completed goals, roadmap completion, latest readiness score, confidence trend, roadmap count, and weekly coaching count.
- Analytics events include career goal creation/update, career assessment, roadmap creation, skill gap creation, learning recommendation creation, and weekly coaching creation.

Privacy and safety:

- Career Coach uses profile, resume, portfolio, certificates, learning, and goal context only through server-side service logic.
- Private reasoning and raw prompts are not exposed.
- Recruiter summaries are permission-controlled and expose high-level growth signals only.
- Feature flags and budget policies can disable or limit Career Coach operations.

Manual testing:

1. Sign in as a student and open `/ai/career/goals`.
2. Create a goal such as `Become Data Analyst`.
3. Open `/ai/career` and run assessment, skill gap, and weekly coaching.
4. Open `/ai/career/roadmap` and generate a 6-month roadmap.
5. Open `/ai/career/history` and confirm records appear.
6. Disable the `career_advice` AI feature flag for a user and confirm assessment is blocked.
7. Set a strict AI budget policy and confirm Career Coach requests are blocked.

Known AI Career Coach limitations:

- Generated plans are guidance, not guaranteed employment outcomes.
- Course recommendation scoring is lightweight and should evolve into a stronger matching model.
- Recruiter summaries are high-level and should not be used for automated hiring decisions.
- Streaming UI is prepared at the product level but the first screens use request/response loading states.
- Roadmap progress updates are manual/foundation-level and should be linked to real course/project/job activity in the next pass.

## AI Product Pass 5 - AI Recruiter Copilot

AI Recruiter Copilot adds hiring-side intelligence on top of the centralized AI Platform. Candidate analysis, ranking, comparison, job description analysis, interview planning, and pipeline insights all route through `AIService`, preserving provider abstraction, moderation, privacy redaction, feature flags, budget enforcement, usage tracking, audit logging, AI analytics, and evaluation-ready request records.

Architecture:

- `AIRecruiterReport` stores recruiter AI outputs with report type, organization, job, candidate, candidate IDs, score, confidence, fairness notes, disclaimer, model name, estimated cost, and a link to the underlying `AIRequest`.
- `AIRecruiterCopilotService` is the sole orchestration point for recruiter AI. It gathers permitted candidate/job context, calls `AIService`, creates a report, tracks analytics, and writes audit logs.
- Candidate access is enforced through `CandidateVisibilityService`, including profile visibility, organization access, entitlement checks, unlock state, and platform admin override.
- Job access is enforced through `PermissionService.can_manage_job`.

Recruiter Copilot APIs:

- `POST /api/v1/ai/recruiter/candidate-analysis/`
- `POST /api/v1/ai/recruiter/candidate-ranking/`
- `POST /api/v1/ai/recruiter/candidate-comparison/`
- `POST /api/v1/ai/recruiter/job-analysis/`
- `POST /api/v1/ai/recruiter/interview-plan/`
- `POST /api/v1/ai/recruiter/pipeline-insights/`
- `GET /api/v1/ai/recruiter/history/`
- `GET /api/v1/ai/recruiter/analytics/`

Frontend screens:

- `/ai/recruiter` shows recruiter AI usage, recent reports, and pipeline insight generation.
- `/ai/recruiter/candidates` supports candidate analysis, job-based ranking, and candidate comparison.
- `/ai/recruiter/jobs` supports job description intelligence and recruiter interview plans.
- `/ai/recruiter/history` lists saved reports and aggregate AI cost/score/confidence metrics.
- `/recruiter/dashboard` now includes a Recruiter Copilot entry point.

Candidate scoring:

- The first scoring layer combines skill overlap, resume evidence, portfolio projects, certificates, and learning activity.
- The AI-generated summary is stored alongside deterministic evidence so UI/tests have stable fields while keeping provider output available.
- Scores are advisory and include confidence and explainability.

Ranking methodology:

- Candidates can be sorted by best fit, highest confidence, highest growth potential, or highest learning activity.
- Rankings expose matched skills, missing skills, explanation, confidence, fairness warning, and disclaimer.
- The ranking response intentionally does not include an auto-reject action or recommendation.

Fairness safeguards:

- Every ranking/report includes a warning that AI must not automatically reject candidates.
- The service instructs AI not to recommend hiring based solely on protected characteristics.
- Outputs must expose uncertainty via confidence and explainability.
- Recruiters must use structured interviews and human review before decisions.

Privacy:

- Recruiter AI can only analyze candidates visible through `CandidateVisibilityService`.
- Private files, prompts, and raw internal reasoning are not exposed in frontend reports.
- Recruiter summaries are organization-scoped and entitlement-aware.

Enterprise permissions:

- Recruiters and company admins can use copilot features only inside permitted organizations and jobs.
- Platform admins can inspect reports globally for governance.
- Pipeline insights require organization access through recruiter, company admin, report viewer, export manager, or platform admin roles.

Manual testing:

1. Sign in as a recruiter with an active organization entitlement.
2. Open `/ai/recruiter` and generate pipeline insights with an organization ID.
3. Open `/ai/recruiter/candidates` and run candidate analysis with a visible/unlocked candidate.
4. Run candidate ranking with a job ID and multiple candidate IDs.
5. Run candidate comparison and confirm fairness warning/disclaimer appear.
6. Open `/ai/recruiter/jobs` and analyze an existing job.
7. Create an interview plan for a candidate/job.
8. Open `/ai/recruiter/history` and confirm reports, scores, confidence, and cost summary.
9. Disable `application_review` or `job_matching` feature flags and confirm affected actions are blocked.
10. Apply a strict AI budget policy and confirm copilot requests are blocked.

Known AI Recruiter Copilot limitations:

- Scoring is an explainable foundation, not a validated hiring model.
- Candidate context is intentionally conservative and may miss private evidence unless the recruiter has authorization.
- Ranking quality depends on the completeness of job skills, resumes, portfolios, certificates, and application history.
- Bias detection is prompt/policy-level in this pass; deeper fairness audits and adverse-impact reporting are still needed.
- Frontend inputs currently use IDs; future passes should add candidate/job pickers.
- Streaming UI is prepared conceptually but current pages use standard loading states.

## AI Product Pass 6 - AI Learning Tutor

AI Learning Tutor turns the centralized AI Platform into a learner-facing companion connected to courses, lessons, quiz attempts, and career-oriented study planning. All tutor, summary, quiz, feedback, instructor-tool, and study-plan operations call `AIService`, preserving provider abstraction, moderation, privacy redaction, feature flags, budget enforcement, usage tracking, audit logging, AI analytics, and evaluation-ready request records.

Architecture:

- `AILearningTutorSession` stores course tutor interactions with course, lesson, question, answer, mode, concepts, confidence, model, cost, and `AIRequest`.
- `AILessonIntelligence` stores lesson summaries, key concepts, glossary, formulas, common mistakes, prerequisites, objectives, estimated study time, content hash, and current/stale state.
- `AIStudyPlan` stores personalized daily, weekly, or monthly plans, pace, available study time, deadline, milestones, weak concepts, recommended lessons, confidence, model, and cost.
- `AIGeneratedQuiz` stores AI-generated reviewable quizzes separately from instructor-created quiz questions.
- `AIQuizFeedback` stores AI explanations, correct reasoning, weak topics, recommended lessons, next actions, confidence, model, and cost.
- `AILearningTutorService` owns context gathering, permission checks, AI calls, analytics, audit logs, and deterministic fallback structures.

Learning Tutor APIs:

- `POST /api/v1/ai/learning/course-tutor/`
- `POST /api/v1/ai/learning/lesson-summary/`
- `POST /api/v1/ai/learning/study-plan/`
- `POST /api/v1/ai/learning/quiz-generation/`
- `POST /api/v1/ai/learning/quiz-feedback/`
- `POST /api/v1/ai/learning/instructor-tools/`
- `GET /api/v1/ai/learning/history/`
- `GET /api/v1/ai/learning/analytics/`

Frontend screens and enhancements:

- `/ai/learning` provides course tutor, lesson intelligence, quiz generation, and quiz feedback actions.
- `/ai/learning/plans` generates personalized study plans.
- `/ai/learning/history` lists tutor sessions, study plans, and quiz feedback.
- Lesson player uses the new centralized tutor endpoint through `TutorChat`.
- Lesson player links to AI study tools with course and lesson context.
- Quiz results include an AI feedback action.

Lesson context:

- Course context includes title, level, language, descriptions, tags, requirements, learning outcomes, and ordered lesson metadata.
- Lesson context includes title, type, content, and position.
- Lesson intelligence is cached by content hash and can be regenerated when content changes.
- The structure is ready for future RAG by concentrating context assembly in `AILearningTutorService`.

Quiz generation:

- AI-generated quizzes are stored separately from instructor-created quizzes and are not published automatically.
- Supported generated question foundations include multiple choice, true/false, short answer, fill in blanks, and coding foundation.
- Instructor review is required before using AI-generated quiz content operationally.

Study plans:

- Plans consider enrollments, completed lessons, quiz results, career goal, available study time, preferred pace, and deadline.
- Cadence supports daily, weekly, and monthly plans with milestone tracking.

Analytics:

- Tracks tutor sessions, questions asked, concepts mastered, weak concepts, learning streak, study time, quiz improvement, AI usage, cost, and confidence.
- Analytics events include tutor use, lesson intelligence generation, study plan creation, quiz generation, quiz feedback, and instructor tool use.

Privacy and cost controls:

- Learners must be enrolled or otherwise permitted to access the course/lesson.
- Instructors must own the course for instructor tools and quiz generation.
- Raw prompts are not exposed in the frontend.
- `course_tutor` and `learning_recommendations` feature flags and budget policies can block or limit operations.

Manual testing:

1. Enroll in a published course and open a lesson player.
2. Click `Ask AI tutor`, ask a lesson question, and confirm the response is saved.
3. Open `/ai/learning?course={course_id}&lesson={lesson_id}` and run tutor, lesson summary, quiz feedback, and quiz generation actions.
4. Open `/ai/learning/plans` and generate a weekly study plan.
5. Submit a course quiz and click `AI feedback` on the result page.
6. Sign in as the instructor and run an instructor AI tool for a lesson.
7. Disable the `course_tutor` feature flag for a user and confirm tutor requests are blocked.
8. Apply a strict `course_tutor` budget policy and confirm requests are blocked.

Known AI Learning Tutor limitations:

- Educational accuracy is not externally validated yet.
- Generated quizzes are reviewable drafts, not publish-ready assessment authority.
- Study plans use lightweight progress and quiz context; deeper scheduling and calendar integration are not present.
- RAG now has a central knowledge platform, but production-grade vector infrastructure and automated source indexing are still evolving.
- Streaming-ready UI is planned, but current tutor calls use request/response loading.
- Course/lesson selection on `/ai/learning` still uses IDs outside the lesson-player shortcut.

## AI Knowledge and RAG Platform

Purpose:

- The knowledge platform centralizes context retrieval for AI Tutor, Resume AI, Portfolio AI, Interview Coach, Career Coach, and Recruiter Copilot.
- AI generation still routes through `AIService`, so moderation, privacy redaction, feature flags, budget enforcement, usage tracking, audit logging, analytics, and evaluation remain the control plane.

Knowledge collections:

- Supported collection types include courses, lessons, quizzes, career tracks, resumes, portfolios, jobs, skills, certificates, FAQs, policies, organization documents, and future document collections.
- `KnowledgeCollection` stores collection type, organization scope, embedding version, vector backend, active status, and metadata.
- `KnowledgeDocument` stores source type/id, title, raw text, redacted text, version, checksum, visibility, index status, embedding version, and last indexed timestamp.
- `KnowledgeChunk` stores chunk text, embedding payload, token count, and ordering.
- `RetrievalEvent` records retrieval latency, confidence, result counts, cache readiness, citations, missing knowledge, and metadata.

Index lifecycle:

- Current statuses are queued, indexing, indexed, failed, and stale.
- Indexing redacts private data before embedding and stores privacy findings in metadata.
- Reindexing updates by `(collection, source_type, source_id)` rather than duplicating documents.
- Course indexing covers the course document plus lesson documents.
- Manual reindexing is available through `/api/v1/ai/knowledge/reindex/` for platform admins or permitted organization managers.

Vector providers:

- The provider abstraction supports `local`, `pgvector`, and `opensearch` backends.
- The current `pgvector` and `opensearch` adapters are provider-ready wrappers over deterministic local embeddings until the infrastructure provider is configured.
- Future Pinecone and Qdrant adapters should implement the same backend interface without changing AI product code.

Retrieval:

- `RetrievalService` supports semantic, keyword, and hybrid search.
- Hybrid scoring combines deterministic vector similarity with keyword overlap.
- Permission filtering allows public documents, organization documents for authorized organization users, private documents for owners when explicitly requested, and platform admin override.
- Retrieval returns citations, confidence, missing knowledge markers, and analytics events.

Citations:

- Citations include document id, chunk id, collection type, source type, source id, title, score, confidence, and document metadata.
- AI prompts instruct the model to cite only retrieved sources when citations are requested.
- The system does not fabricate citations when retrieval returns no context.

AI context builder:

- `AIContextBuilder` maps AI features to relevant collection types and assembles reusable retrieved context.
- `AIService.generate_text` calls the context builder before prompt rendering.
- If no indexed context exists, prompts continue without injected RAG context to preserve existing behavior.

Frontend and admin:

- `/ai/admin` now shows knowledge collections, indexed document/chunk counts, embedding versions, recent retrievals, sample indexing, and retrieval testing.
- The course tutor chat shows up to three citations when the tutor response includes retrieved sources.

Manual testing:

1. Sign in as platform admin and open `/ai/admin`.
2. Click `Index sample` in the Knowledge and RAG panel.
3. Run `Test retrieval` and confirm confidence plus citations appear.
4. Open a lesson with `TutorChat`, ask a related question, and confirm sources appear when indexed context matches.
5. Call `/api/v1/ai/knowledge/index-status/` and `/api/v1/ai/knowledge/embedding-status/` to inspect backend status.
6. Try a private knowledge document as owner, outsider, and platform admin to confirm visibility behavior.

Known RAG limitations:

- pgvector and OpenSearch adapters are interface-ready but not backed by live external infrastructure yet.
- Automatic indexing is not wired to every content save signal.
- Ranking is intentionally lightweight and needs learned reranking or stronger lexical search before public-scale use.
- Citations identify source chunks but do not yet expose rich lesson/page anchors in every product UI.
- There is no retention or stale-document cleanup command yet.

## Production RAG and Knowledge Freshness

Vector setup:

- `AI_VECTOR_BACKEND` controls backend selection. Supported values are `local`, `pgvector`, and `opensearch`.
- Local development and tests default to deterministic local embeddings.
- Non-debug environments default to `pgvector` unless `AI_VECTOR_BACKEND` is explicitly set.
- `AI_VECTOR_DIMENSIONS` controls expected embedding dimensions and is validated during indexing.
- `AI_EMBEDDING_VERSION` is stored on collections and documents so future model upgrades can coexist with existing vectors.
- `/api/v1/ai/knowledge/vector-health/` exposes provider health for platform admins without secrets.

Automatic indexing lifecycle:

- Signals index or reindex courses, lessons, jobs, career resumes, portfolios, portfolio skills/projects, career tracks, quiz questions, and certificates on save.
- Deletes mark existing knowledge documents stale instead of removing them immediately.
- `python manage.py reindex_ai_knowledge` supports `--collection`, `--source-type`, `--organization-id`, `--limit`, and `--dry-run`.
- `--source-type stale` and `--source-type failed` retry documents that need operational attention.
- Signal failures are logged and do not block user-facing source saves.

Freshness model:

- Knowledge documents track source `updated_at`, indexed timestamp, stale status, checksum, failed reason, last successful reindex, and freshness score.
- Freshness is `100` when indexed after the source update, lower when stale or checksum changes, and `0` for failed indexing.
- `/api/v1/ai/knowledge/index-status/` returns collection counts, vector backend status, stale/failed documents, and aggregate freshness.

Privacy and tenant isolation:

- Public knowledge is globally retrievable.
- Organization documents require matching organization scope and organization access.
- Private resumes and portfolios are owner-only unless candidate visibility rules grant recruiter access through an organization context.
- Private course and lesson knowledge is retrievable by the instructor or enrolled learners only.
- Platform admins retain override access for audit and support.
- Citation payloads expose safe source title/type/freshness/deep link only; raw hidden metadata is not returned.

Retrieval performance controls:

- Retrieval events now track latency, source count, chunk count, context size, cache hit, and timeout status.
- Retrieval cache defaults to `AI_RETRIEVAL_CACHE_SECONDS=300`.
- Retrieval timeout defaults to `AI_RETRIEVAL_TIMEOUT_MS=750`.
- Feature context size is controlled through `context_limit` and collection mapping in `AIContextBuilder`.

Retrieval evaluation:

- `RetrievalEvaluationDataset` stores query cases with expected document, chunk, citation, source type, minimum confidence, and feature.
- `RetrievalEvaluationService.run_dataset` records pass/fail, ranking position, retrieved citations, confidence, and aggregate pass rate.
- Platform admins can create datasets and run them through `/api/v1/ai/knowledge/retrieval-evaluations/` and `/api/v1/ai/knowledge/retrieval-evaluations/run/`.

Operational runbook:

1. Configure `AI_VECTOR_BACKEND=pgvector`, `AI_VECTOR_DIMENSIONS`, and `AI_EMBEDDING_VERSION`.
2. Run migrations.
3. Run `python manage.py reindex_ai_knowledge --dry-run --limit 50`.
4. Run targeted reindexing by source type, for example `python manage.py reindex_ai_knowledge --source-type course --limit 100`.
5. Open `/ai/admin` and verify backend health, freshness, stale documents, failed documents, and retrieval test results.
6. Create a retrieval evaluation dataset for critical queries and run it before beta releases.
7. Monitor stale/failed counts and retry with `--source-type stale` or `--source-type failed`.

## Auth Flow

Login, registration, and Google auth return access tokens and user metadata while placing refresh tokens in an `HttpOnly` cookie. Refresh and logout require the readable auth CSRF cookie to match `X-CSRFToken` when cookie-backed refresh tokens are used. Refresh tokens must not be returned in JSON response bodies.

## Testing Commands

Backend:

```powershell
$env:SECRET_KEY='local-test-secret-with-at-least-32-bytes'
$env:DATABASE_URL='sqlite:///test_local.sqlite3'
$env:REDIS_URL='redis://localhost:6379/0'
$env:CELERY_BROKER_URL='redis://localhost:6379/1'
$env:ALLOWED_HOSTS='localhost,127.0.0.1,testserver'
$env:GOOGLE_OAUTH_CLIENT_ID='test-google-client-id'
$env:GOOGLE_OAUTH_CLIENT_SECRET='test-google-secret'
python -m pytest
```

Frontend:

```powershell
npm ci
npm run type-check
npm run lint
npm run build
npm audit --audit-level=high --omit=dev
```

## Dependency Audit

Next.js has been updated within the existing 14.x line. CI now treats frontend production dependency audit failures as blocking so dependency risk is visible before deployment.
