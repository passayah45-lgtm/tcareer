# Course Authoring and Academic Review

This document describes the Version 1.0 course authoring and academic review foundation.

## Scope

This pass adds production-oriented controls around existing course authoring. It does not publish new courses, add new career tracks, or generate large course content automatically.

## Authoring Model

Instructors can create and edit draft courses and lessons through the existing instructor workspace. Course content is now supported by these foundation models:

- `CourseReview`: academic review decisions for a course.
- `LessonVersion`: snapshots of lesson title, type, and content.
- `CourseProject`: final project instructions, deliverables, rubric, criteria, and approval state.
- `ResourceLibraryItem`: instructor-owned resources that can be attached to courses.

Lessons include review state plus draft and published version counters. Publishing a lesson through the inline editor is blocked unless the lesson is academically approved or already in a published review state.

## Review Lifecycle

Supported content review states:

- `draft`
- `needs_review`
- `under_review`
- `changes_requested`
- `approved`
- `rejected`
- `published`
- `archived`

Typical lifecycle:

1. Instructor drafts course and lessons.
2. Instructor captures lesson versions as meaningful edits are made.
3. Instructor submits the course for review.
4. Reviewer approves, rejects, or requests changes.
5. Lesson review decisions are recorded separately.
6. Final project is approved where required.
7. Course publish validation checks all gates.

## Publishing Checklist

`CourseService.publish_validation_errors` blocks publishing when:

- Course has no active instructor.
- Description or short description is missing.
- Learning objectives are missing.
- Prerequisites are missing.
- No lessons are published.
- Published lessons have empty content.
- Published lessons contain review-required markers.
- Assessments exist but fewer than five approved certificate-eligible questions exist.
- Assessment explanations contain review-required markers.
- A required final project is not approved.
- Latest academic course review is not approved.
- Any non-deleted lesson is still draft, under review, changes requested, or rejected.

## Assessment Metadata

Question bank records now support:

- `category`
- `reusable_key`
- `learning_objective`

These fields are available in admin, question serializers, and bulk creation. Certificate-eligible questions still require approval.

## Instructor Content Quality Page

Frontend route:

- `/instructor/content-quality`

The page shows:

- Total courses reviewed.
- Publish-ready count.
- Average quality score.
- Instructor review analytics.
- Priority courses with the lowest readiness score.
- Per-course readiness checks and blockers.
- Submit-for-review action.

## API Summary

Course authoring and review APIs:

- `GET /api/v1/courses/author-analytics/`
- `GET /api/v1/courses/quality-dashboard/`
- `GET /api/v1/courses/{course_id}/quality/`
- `GET /api/v1/courses/{course_id}/reviews/`
- `POST /api/v1/courses/{course_id}/reviews/submit/`
- `POST /api/v1/courses/{course_id}/reviews/decision/`
- `GET|POST /api/v1/courses/{course_id}/project/`
- `POST /api/v1/courses/{course_id}/project/review/`
- `GET|POST /api/v1/courses/resources/`
- `GET|POST /api/v1/courses/{course_id}/lessons/{lesson_id}/versions/`
- `POST /api/v1/courses/{course_id}/lessons/{lesson_id}/versions/compare/`
- `POST /api/v1/courses/{course_id}/lessons/{lesson_id}/versions/{version_id}/rollback/`
- `POST /api/v1/courses/{course_id}/lessons/{lesson_id}/review/`

## Manual Testing

1. Sign in as an instructor.
2. Open `/instructor/content-quality`.
3. Confirm draft courses show blockers instead of publish-ready state.
4. Open a course and ensure it can still be edited.
5. Submit a course for review from the content quality page.
6. In Django admin, approve the course academic review.
7. Approve/publish all lessons through the review API or admin.
8. If the course requires a final project, configure and approve the project.
9. Run publish validation and confirm the course cannot bypass missing gates.
10. Confirm learner/community course reviews remain separate from academic course reviews.

## Current Limitations

- File-backed resource uploads are not implemented in this pass; resources can still store URL or storage key metadata.
- Review UI is focused on dashboard readiness. Deep inline review controls in the course editor are still limited.
- AI author assistant remains dependent on the existing AI platform and is not expanded here.
- No automatic content publishing is performed.
- No automatic deletion or retention workflow exists for lesson versions or resource records.
