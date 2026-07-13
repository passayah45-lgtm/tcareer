# Data Analyst Curriculum Content

This runbook covers the production-safe Data Analyst curriculum content seed. It turns the 12 Data Analyst course shells into structured draft lessons and review-required quiz questions without creating fake learner activity.

## Scope

The curriculum covers:

- Excel for Data Analysis
- SQL for Data Analysis
- Python Fundamentals
- Statistics for Data Analysis
- Python for Data Analysis
- Data Cleaning and Preparation
- Data Visualization with Power BI
- Data Visualization with Tableau
- Business Intelligence Fundamentals
- Data Analytics Portfolio Project
- Resume Preparation for Data Analysts
- Interview Preparation for Data Analysts

Each course definition includes objectives, prerequisites, module titles, lesson order, lesson objectives, starter lesson body, practice tasks, and review-required assessment questions.

## Model Fit

Current learning models include `Course`, `Lesson`, `VideoLesson`, `Enrollment`, `LessonProgress`, `QuizQuestion`, `QuizAttempt`, and `CourseRating`.

There is no separate module/section model. Modules are represented in the curriculum definition file and reflected in lesson ordering/content.

There is no first-class quiz draft/review field. Seeded quiz explanations are prefixed with `[REVIEW REQUIRED]`, courses remain draft, and no certificate is issued. Instructors must review questions before using them for certificate decisions.

## Commands

Dry run one course:

```bash
python manage.py seed_data_analyst_course_content \
  --course excel-for-data-analysis \
  --instructor-email instructor@example.com \
  --dry-run
```

Seed one course as draft/review-required content:

```bash
python manage.py seed_data_analyst_course_content \
  --course excel-for-data-analysis \
  --instructor-email instructor@example.com \
  --confirm-production
```

Seed all Data Analyst courses:

```bash
python manage.py seed_data_analyst_course_content \
  --all-courses \
  --instructor-email instructor@example.com \
  --confirm-production
```

Update existing content intentionally:

```bash
python manage.py seed_data_analyst_course_content \
  --all-courses \
  --instructor-email instructor@example.com \
  --update-existing \
  --confirm-production
```

Mark content review-ready without publishing:

```bash
python manage.py seed_data_analyst_course_content \
  --all-courses \
  --instructor-email instructor@example.com \
  --publish-ready \
  --confirm-production
```

Readiness report:

```bash
python manage.py course_content_readiness_report --track data-analyst
python manage.py course_content_readiness_report --course excel-for-data-analysis --json
python manage.py course_content_readiness_report --track data-analyst --fail-on-not-ready
```

## Safety Controls

- No users are created.
- No enrollments, learner progress, reviews, ratings, certificates, applications, or analytics are created.
- Production writes require `--confirm-production`.
- `--dry-run` prints the plan and writes nothing.
- Writes are transaction-wrapped.
- Missing course shells stop the command.
- Invalid or unauthorized instructors stop the command.
- Existing manual lessons remain unchanged unless `--update-existing` is passed.
- Lessons are created as text lessons with `is_published=False`.
- Courses are forced to draft when metadata is updated.
- Quiz questions are marked review-required in explanation text.
- Audit logs use source `production_data_analyst_curriculum`.

## Production Execution

1. Commit and push reviewed code.
2. SSH into the VPS.
3. Pull the reviewed commit.
4. Run migrations if needed.
5. Confirm the catalog exists with `career_track_coverage_report --track data-analyst`.
6. Run content dry run.
7. Review the plan.
8. Run the confirmed content seed without publishing.
9. Run the readiness report.
10. Review content manually in Django admin or instructor UI.
11. Correct content and assessments.
12. Publish approved lessons.
13. Publish approved courses.
14. Run track coverage.
15. Verify live course and track pages.

## Rollback

Do not delete learner progress or real production content.

Safe rollback options:

- Return lessons to draft.
- Return courses to draft.
- Archive affected courses.
- Detach courses from the track if needed.
- Keep audit logs for traceability.

## Known Limitations

- Modules are definition-level only until a real module/section model exists.
- Quiz questions lack a real draft/review status field.
- Starter lessons are reviewable foundations, not final polished courseware.
- No media resources are seeded.
- No automatic publishing is performed.
