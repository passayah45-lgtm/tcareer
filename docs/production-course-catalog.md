# Production Course Catalog and Career Track Attachment

This runbook covers the production-safe course catalog seed used to attach real courses to career tracks without creating fake users, enrollments, applications, interviews, reviews, analytics, or demo activity.

## Commands

Dry run:

```bash
python manage.py seed_production_course_catalog \
  --track data-analyst \
  --instructor-email instructor@example.com \
  --dry-run
```

Write draft courses:

```bash
python manage.py seed_production_course_catalog \
  --track data-analyst \
  --instructor-email instructor@example.com \
  --confirm-production
```

Write published courses after reviewing required fields:

```bash
python manage.py seed_production_course_catalog \
  --track data-analyst \
  --instructor-email instructor@example.com \
  --publish \
  --confirm-production
```

Update existing seeded courses and attachment ordering:

```bash
python manage.py seed_production_course_catalog \
  --track data-analyst \
  --instructor-email instructor@example.com \
  --publish \
  --update-existing \
  --confirm-production
```

Coverage report:

```bash
python manage.py career_track_coverage_report
python manage.py career_track_coverage_report --track data-analyst --json
python manage.py career_track_coverage_report --fail-on-empty
```

## Instructor Requirement

The seed command never creates an instructor. The operator must provide an existing active user with one of these roles:

- `instructor`
- `platform_admin`
- `super_admin`
- `admin`
- staff user

If the user does not exist, is inactive, or has a student/recruiter role, the command fails before writing data.

## Safety Controls

- The command creates only `Course` and `TrackCourse` records.
- It does not create users, enrollments, applications, interviews, reviews, analytics events, or notifications.
- In production (`DEBUG=False`), writes require `--confirm-production`.
- `--dry-run` prints the plan and writes nothing.
- All writes run inside a database transaction.
- Existing courses are preserved unless `--update-existing` is passed.
- Manually attached courses are not detached.
- Duplicate attachments are prevented by the existing `track, course` uniqueness rule.
- Course definitions are validated with Django model validation before writes.
- Audit logs are written for course seed, update, publish, track attachment, and attachment order changes.
- Seeded records are identified by deterministic production catalog slugs and audit metadata source `production_course_catalog_seed`.

## Publish Workflow

The default is draft. Public track APIs hide draft attached courses.

Use `--publish` only when the operator has reviewed the catalog plan and is comfortable exposing the course shells publicly. This seed does not create lessons. A published course without lessons can appear in the catalog, so the preferred first production run is draft unless launch timing requires track counts immediately.

## Data Analyst Catalog

The first supported production catalog covers the `data-analyst` track:

1. Excel for Data Analysis
2. SQL for Data Analysis
3. Python Fundamentals
4. Statistics for Data Analysis
5. Python for Data Analysis
6. Data Cleaning and Preparation
7. Data Visualization with Power BI
8. Data Visualization with Tableau
9. Business Intelligence Fundamentals
10. Data Analytics Portfolio Project
11. Resume Preparation for Data Analysts
12. Interview Preparation for Data Analysts

## Production Verification

1. SSH into the VPS.
2. Pull the reviewed commit.
3. Run migrations if future migrations exist.
4. Run a dry run with the real instructor email.
5. Review planned course and attachment changes.
6. Run the confirmed seed.
7. Run `career_track_coverage_report --track data-analyst`.
8. Rebuild only if frontend code changed.
9. Verify:
   - `/tracks`
   - `/tracks/data-analyst`
   - `/api/v1/tracks/`
   - `/api/v1/tracks/data-analyst/`

## Rollback Guidance

Do not blindly delete production data.

Safe rollback options:

- If courses were created as draft, leave them draft or archive them in Django admin.
- If courses were published by mistake, change status back to draft or archived.
- To hide courses from a track, remove only the affected `TrackCourse` attachments after confirming no manual production work depends on them.
- Prefer recording rollback notes in audit/admin records and keeping the course shells for traceability.

## Known Limits

- The initial catalog only covers `data-analyst`.
- The seed creates course shells, not full lesson content.
- There is no first-class course metadata field, so source marking is done through slugs and audit metadata.
- Public track course counts intentionally include only published, non-deleted courses.
