# Instructor Review Workspace and Academic Governance

This pass turns the academic review foundation into a daily workflow for instructors, academic reviewers, and platform administrators.

## Reviewer Roles

Supported reviewer capabilities:

- `platform_academic_reviewer`: can review academic content across the platform.
- `organization_academic_reviewer`: scoped to one organization.
- `course_reviewer`: assigned to specific course review work.
- `subject_reviewer`: intended for subject-area review assignment.
- `lead_reviewer`: can assign and reassign reviews within permitted scope.

Instructors cannot approve their own course, lesson, question, project, or resource unless an explicit superuser override is used. Platform overrides are audited.

Reviewer profiles also define:

- `max_active_assignments`: default 25.
- `automatic_assignment_enabled`: disabled by default.
- `subject_tags`: optional subject matching, such as `excel`.
- `organization`: optional organization scope.

Assignments now enforce conflict checks before creation. A reviewer cannot be assigned to their own course content, cannot exceed their active assignment limit, and cannot receive subject-scoped work outside their configured subject tags.

## Assignment Workflow

Review assignments support:

- target type: course, lesson, assessment, project, resource
- assigned reviewer
- assigned by
- due date
- priority
- status
- reassignment history
- completion date

Review queue filters support assigned-to-me, status, priority, target type, course, and overdue.

Dashboard metrics include assigned count, overdue count, due soon, high priority, average review time, changes requested, completed reviews, subject distribution, and organization distribution. These are workload-management metrics only; the platform should not expose public reviewer rankings.

Automatic assignment is foundation-ready but disabled by default. When enabled, the selector chooses an active reviewer with matching subject and organization scope and the lowest active workload.

Overdue reviews can be escalated by an academic admin or permitted lead reviewer. Escalation raises priority to urgent, records escalation metadata, and writes an academic audit event.

## Review States

Content states:

- `draft`
- `needs_review`
- `under_review`
- `changes_requested`
- `approved`
- `rejected`
- `published`
- `archived`

Reviewer decisions:

- `approve`
- `approve_minor_edits`
- `request_changes`
- `reject`
- `escalate`

Decision mapping:

- approve / approve minor edits -> approved
- request changes -> changes requested or review required
- reject -> rejected
- escalate -> under review

## Instructor Workflow

Instructor pages:

- `/instructor/content-quality`
- `/instructor/courses/[courseId]/review`
- `/instructor/courses/[courseId]/versions`

Instructors can view blockers, submit/resubmit for review, inspect approval history, and view version history. Editing approved content reopens relevant review state where implemented.

## Reviewer Workflow

Reviewer pages:

- `/reviewer/dashboard`
- `/reviewer/queue`
- `/reviewer/courses/[courseId]`
- `/reviewer/lessons/[lessonId]`
- `/reviewer/questions/[questionId]`
- `/reviewer/projects/[projectId]`

Structured lesson review covers educational accuracy, learning objective alignment, clarity, examples, exercises, resource quality, grammar, accessibility, copyright, and assessment alignment.

## Assessment Approval

Question review now supports structured decision history. Question edits after approval return the question to `review_required`. Certificate eligibility is blocked unless the question is approved.

## Project Approval

Final project structured review supports brief, dataset, deliverables, rubric, passing criteria, submission format, example solution, required resources, and certificate requirement review. Changes to an approved project reopen review.

## Resource Upload Rules

Supported formats:

- CSV, XLSX, PDF, PPTX, DOCX, IPYNB, SQL, TXT, ZIP, PNG, JPG, JPEG, WEBP

Rejected formats:

- executable/script-like extensions such as EXE, DLL, BAT, CMD, SH, MSI, PS1, SCR, JS

Controls:

- MIME validation
- extension validation
- maximum size: 50 MB
- duplicate checksum rejection per owner
- private/course/public visibility
- provider-neutral malware scan status
- authorized download endpoint
- private resources do not expose raw storage keys to learner-facing APIs

Malware scan providers:

- `disabled`: scan is marked skipped. This is not malware protection.
- `mock`: deterministic test adapter; clean files pass and EICAR-like signatures are marked infected.
- `clamav`: adapter placeholder. If configured without a real daemon/client, scan fails closed.
- `external`: reserved for future providers and fails closed until implemented.

Scan states:

- `pending`
- `scanning`
- `clean`
- `infected`
- `failed`
- `skipped`

Approval and download rules:

- executable/script-like extensions remain blocked before upload
- infected resources cannot be approved or downloaded
- failed scans cannot be approved or downloaded by default
- pending scan resources created through the upload flow cannot be downloaded
- course publication blocks resources whose scan status is pending, scanning, infected, or failed
- private storage keys are never returned as the download result; authorized users receive a signed/private download URL when storage supports it

## Academic Audit

Protected page:

- `/platform/academic-audit`

API supports filtering and CSV export of academic governance audit actions.

## Publishing Gates

Publication is blocked unless:

- course has active instructor
- descriptions, objectives, and prerequisites exist
- published lessons exist
- published lessons are not empty
- published lessons have approved/published review state
- published lessons have a published version
- no review-required markers exist
- assessment coverage is approved
- certificate-eligible questions are approved
- final project is approved when required
- resources exist, are approved, and are not rejected
- approved resources have clean scan status, or skipped status only when scanning is disabled
- no unresolved changes requested exist
- latest academic course review is approved

Approval does not publish automatically.

## Version Safety

Lesson versions preserve draft and published version numbers. Rollbacks create an audit event and restore content into draft review state. Existing learner progress remains tied to the lesson record; deeper version-specific learner history is still a future hardening item.

## Manual Testing Guide

1. Create or open a draft instructor course.
2. Open `/instructor/content-quality`.
3. Submit the course for review.
4. Assign a reviewer through `POST /api/v1/courses/reviewer/queue/`.
5. Open `/reviewer/queue`.
6. Review a course at `/reviewer/courses/[courseId]`.
7. Review a lesson at `/reviewer/lessons/[lessonId]?course=[courseId]`.
8. Review an assessment question at `/reviewer/questions/[questionId]?course=[courseId]`.
9. Review a project at `/reviewer/projects/[projectId]?course=[courseId]`.
10. Upload a resource through `/api/v1/courses/resources/upload-url/`.
11. Review the resource.
12. Confirm `/api/v1/courses/[courseId]/publish-blockers/` blocks unapproved items.
13. Confirm `/platform/academic-audit` shows assignment, decision, resource, and blocked publication actions.

## Known Limitations

- Organization-scoped reviewer filtering is foundational and depends on course-to-organization relationships becoming richer.
- File signature and malware scanning are hook-ready but not backed by a real scanning provider yet.
- Reviewer UI is workflow-capable, not final polished product design.
- Learner progress is protected from content deletion, but not yet tied to immutable per-version lesson snapshots.
- CSV export is capped in code by query slicing and should receive export job handling later.

## Academic Override Policy

Allowed platform academic admin override reasons:

- reassignment
- emergency publication rollback
- reviewer absence
- incorrect stuck state
- security issue
- legal issue

Prohibited overrides:

- approve unreviewed certificate questions
- bypass infected resource checks
- bypass missing lesson content
- erase or rewrite audit history

Every override records actor, timestamp, target, reason, previous state, new state, metadata, and audit event.

## Production Validation Procedure

Before deploying academic governance changes:

1. Confirm production branch and reviewed SHA.
2. Confirm the working tree is clean.
3. Create a PostgreSQL backup.
4. Verify backup with `pg_restore -l`.
5. Record current course, lesson, question, review, assignment, resource, enrollment, and certificate counts.
6. Inspect pending migrations.
7. Stop if backup, database, Redis, storage, reviewed SHA, or migration checks fail.

After deployment:

1. Apply migrations in reviewed order.
2. Run Django system check.
3. Run migration drift check.
4. Run production smoke check.
5. Run health checks.
6. Run PostgreSQL-backed governance tests.
7. Validate reviewer dashboard, queue, course review, lesson review, question review, project review, instructor response, versions, content quality, and academic audit pages.

## Excel Approval Procedure

Excel for Data Analysis must remain draft until:

- all 10 lessons have academic review decisions
- all 23 questions have review decisions
- enough certificate-eligible questions are approved
- the final project is approved and evaluable
- resources exist, are reviewed, and have acceptable scan status
- publication blockers are checked without publishing
- certificate gates pass
- a separate operator decision approves publication

Decision labels:

- keep draft
- changes requested
- under academic review
- academic review approved
- ready for controlled learner test
- ready to publish

The platform must not choose `ready to publish` merely because automated tests pass.
