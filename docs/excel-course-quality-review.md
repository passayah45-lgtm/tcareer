# Excel Course Quality Review

## Scope

This document covers the reviewed foundation for `excel-for-data-analysis`.
It does not publish the course, enroll learners, issue certificates, or seed
other Data Analyst courses.

## Lesson Structure

Every Excel lesson now follows the same review-ready structure:

- measurable objective
- clear introduction
- Excel-specific explanation
- worked example
- common mistakes
- guided practice
- independent practice
- expected output
- validation checklist
- Excel version note
- recap

The ten lessons remain draft until an instructor manually reviews them.

## Dataset

Dataset: `backend/apps/courses/resources/excel_retail_sales_sample.csv`

The dataset is synthetic, deterministic, and contains 150 rows. It includes:

- inconsistent region casing
- leading/trailing spaces
- blank discounts
- missing categories
- mixed date formats
- duplicate order rows

Generate it with:

```bash
python manage.py generate_excel_course_dataset --force
```

Useful options:

```bash
python manage.py generate_excel_course_dataset --output /tmp/excel.csv --rows 150 --seed 20260714
```

The command refuses to overwrite an existing file unless `--force` is used.

## Exercises

Every lesson defines:

- task
- input
- steps
- expected result
- validation checklist
- common errors

Exercises reference the synthetic retail dataset where practical. No exercise
requires a private or missing file.

## Assessment Bank

The Excel assessment bank contains 23 draft questions:

- 12+ multiple-choice knowledge questions
- 4 applied formula questions
- 3 data-cleaning scenarios
- 2 pivot-table interpretation questions
- 2 chart-selection questions

All seeded questions default to `review_required` and
`is_certificate_eligible=False`. Instructors or platform admins must approve
questions before they can count toward certificate eligibility.

## Review Workflow

Question review fields:

- `review_status`: `draft`, `review_required`, `approved`, `rejected`
- `reviewed_by`
- `reviewed_at`
- `review_notes`
- `is_certificate_eligible`

Normal question edits cannot silently approve a question. A question must go
through the explicit approval flow, and approval is audited.

## Certificate Rules

Certificates are blocked unless:

- the course is published
- published lessons exist
- all published lessons are complete
- at least five approved certificate-eligible questions exist
- no assessment explanation contains `[REVIEW REQUIRED]`
- the learner passed the approved quiz
- final project completion is verified when a course requires it

## Publish Checklist

Before publishing a course:

- instructor must be active
- description and short description must exist
- learning objectives must exist
- prerequisites must exist
- at least one published lesson must exist
- published lessons must not be empty
- public lesson content must not contain review-required markers
- courses with assessments need approved certificate-eligible questions
- assessment content must not contain `[REVIEW REQUIRED]`
- final-project rules must be configured where required

## AI Tutor Evaluation

No production AI provider is configured in this pass. Use staging or local mock
provider testing for:

- relative vs absolute references
- XLOOKUP vs VLOOKUP
- duplicate-row removal
- pivot refresh behavior
- monthly sales trend chart choice

AI tutor availability must not block non-AI course learning.

## Analytics Classification

System events such as `ai_knowledge_document_indexed` are written as:

- `category=operations`
- `source=system`
- `actor_type=system`
- `is_system_event=True`
- `counts_toward_engagement=False`

These events must be excluded from learner engagement, course popularity,
completion, instructor performance, and investor-facing activity metrics.

## Production Update Process

1. Commit and push the reviewed code.
2. Back up the production database.
3. Pull the reviewed commit on the VPS.
4. Run migrations.
5. Run an Excel-only dry run:

```bash
python manage.py seed_data_analyst_course_content \
  --course excel-for-data-analysis \
  --instructor-email admin@tcareer.com \
  --update-existing \
  --fields lesson_content,objectives,exercises,assessments \
  --dry-run
```

6. Review every planned field change.
7. Apply the approved update with `--confirm-production`.
8. Run the readiness report.
9. Review questions manually.
10. Approve questions manually.
11. Run certificate safety checks.
12. Keep the course draft.
13. Prepare one controlled learner test.

## Rollback

Use the latest pre-update database backup. Do not delete course, learner,
progress, quiz, or certificate records manually.
