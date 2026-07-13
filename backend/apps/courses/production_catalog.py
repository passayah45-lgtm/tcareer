"""Production-safe course catalog definitions.

This module intentionally contains catalog metadata only. It must not create
users, enrollments, applications, analytics events, or demo activity.
"""

from __future__ import annotations

from dataclasses import dataclass

from apps.courses.models import CourseLevel
from apps.tracks.models import TrackStage

SOURCE = "production_course_catalog_seed"


@dataclass(frozen=True)
class CatalogCourse:
    title: str
    slug: str
    short_description: str
    description: str
    level: str
    tags: tuple[str, ...]
    requirements: tuple[str, ...]
    what_you_learn: tuple[str, ...]
    price: str = "0.00"
    language: str = "en"


@dataclass(frozen=True)
class TrackAttachment:
    course_slug: str
    position: int
    stage: int
    is_required: bool = True
    notes: str = ""


DATA_ANALYST_COURSES: tuple[CatalogCourse, ...] = (
    CatalogCourse(
        title="Excel for Data Analysis",
        slug="excel-for-data-analysis",
        short_description="Use spreadsheets to clean, analyze, and summarize business data.",
        description=(
            "A practical introduction to Excel for analysts. Students learn formulas, "
            "tables, pivots, charts, data validation, and repeatable analysis habits."
        ),
        level=CourseLevel.BEGINNER,
        tags=("excel", "data-analysis", "spreadsheets", "business-analysis"),
        requirements=("Basic computer literacy",),
        what_you_learn=(
            "Clean and structure spreadsheet data",
            "Build pivot tables and charts",
            "Use formulas for analysis",
            "Prepare simple business reports",
        ),
    ),
    CatalogCourse(
        title="SQL for Data Analysis",
        slug="sql-for-data-analysis",
        short_description="Query relational databases and answer business questions with SQL.",
        description=(
            "Students learn SELECT queries, filtering, joins, aggregations, grouping, "
            "subqueries, and analysis patterns used by data teams."
        ),
        level=CourseLevel.BEGINNER,
        tags=("sql", "databases", "analytics", "data-analysis"),
        requirements=("Comfort using a computer",),
        what_you_learn=(
            "Write SELECT queries",
            "Join related tables",
            "Aggregate and group data",
            "Translate questions into SQL",
        ),
    ),
    CatalogCourse(
        title="Python Fundamentals",
        slug="python-fundamentals",
        short_description="Learn Python syntax, control flow, functions, and data structures.",
        description=(
            "A beginner-friendly Python course focused on the programming foundations "
            "needed before data analysis with Python."
        ),
        level=CourseLevel.BEGINNER,
        tags=("python", "programming", "foundations"),
        requirements=("No prior programming experience required",),
        what_you_learn=(
            "Write basic Python programs",
            "Use lists, dictionaries, and functions",
            "Read and debug Python code",
            "Prepare for data analysis libraries",
        ),
    ),
    CatalogCourse(
        title="Statistics for Data Analysis",
        slug="statistics-for-data-analysis",
        short_description="Understand descriptive statistics, distributions, and confidence.",
        description=(
            "A practical statistics course for analysts covering summary statistics, "
            "sampling, probability, distributions, correlation, and interpretation."
        ),
        level=CourseLevel.BEGINNER,
        tags=("statistics", "analytics", "probability", "data-analysis"),
        requirements=("Basic arithmetic",),
        what_you_learn=(
            "Summarize datasets",
            "Understand distributions",
            "Interpret correlation carefully",
            "Communicate uncertainty",
        ),
    ),
    CatalogCourse(
        title="Python for Data Analysis",
        slug="python-for-data-analysis",
        short_description="Analyze tabular data with Python, pandas, and notebooks.",
        description=(
            "Students use pandas and notebooks to load, inspect, clean, transform, "
            "summarize, and visualize real-world datasets."
        ),
        level=CourseLevel.INTERMEDIATE,
        tags=("python", "pandas", "notebooks", "data-analysis"),
        requirements=("Python fundamentals", "Basic statistics"),
        what_you_learn=(
            "Load data into pandas",
            "Clean and transform datasets",
            "Group and summarize data",
            "Create analysis notebooks",
        ),
    ),
    CatalogCourse(
        title="Data Cleaning and Preparation",
        slug="data-cleaning-and-preparation",
        short_description="Turn messy raw data into trustworthy analysis-ready datasets.",
        description=(
            "A focused course on missing values, duplicates, formats, outliers, "
            "data quality checks, and documenting repeatable preparation steps."
        ),
        level=CourseLevel.INTERMEDIATE,
        tags=("data-cleaning", "data-quality", "pandas", "analytics"),
        requirements=("Python for data analysis or equivalent experience",),
        what_you_learn=(
            "Find and fix data quality issues",
            "Handle missing and duplicate data",
            "Validate cleaned datasets",
            "Document preparation workflows",
        ),
    ),
    CatalogCourse(
        title="Data Visualization with Power BI",
        slug="data-visualization-with-power-bi",
        short_description="Build dashboards and reports that explain business performance.",
        description=(
            "Students learn the fundamentals of Power BI, including data import, "
            "modeling, dashboard layout, visual selection, and stakeholder reporting."
        ),
        level=CourseLevel.INTERMEDIATE,
        tags=("power-bi", "dashboards", "visualization", "business-intelligence"),
        requirements=("Basic data analysis experience",),
        what_you_learn=(
            "Create Power BI reports",
            "Choose effective charts",
            "Design readable dashboards",
            "Present metrics to stakeholders",
        ),
    ),
    CatalogCourse(
        title="Data Visualization with Tableau",
        slug="data-visualization-with-tableau",
        short_description="Create interactive Tableau dashboards for analysis and storytelling.",
        description=(
            "A practical Tableau course covering data connections, calculated fields, "
            "visual design, filters, dashboards, and publishing-ready workbooks."
        ),
        level=CourseLevel.INTERMEDIATE,
        tags=("tableau", "dashboards", "visualization", "analytics"),
        requirements=("Basic data analysis experience",),
        what_you_learn=(
            "Build Tableau worksheets",
            "Create interactive dashboards",
            "Use filters and calculated fields",
            "Tell clear stories with data",
        ),
    ),
    CatalogCourse(
        title="Business Intelligence Fundamentals",
        slug="business-intelligence-fundamentals",
        short_description="Connect metrics, dashboards, and decision-making in organizations.",
        description=(
            "Students learn BI concepts such as KPIs, metric definitions, dashboard "
            "requirements, stakeholder interviews, and reporting governance."
        ),
        level=CourseLevel.INTERMEDIATE,
        tags=("business-intelligence", "kpis", "dashboards", "analytics"),
        requirements=("Basic SQL and visualization skills",),
        what_you_learn=(
            "Define useful KPIs",
            "Gather dashboard requirements",
            "Build reporting workflows",
            "Communicate data tradeoffs",
        ),
    ),
    CatalogCourse(
        title="Data Analytics Portfolio Project",
        slug="data-analytics-portfolio-project",
        short_description="Build a complete analytics project for your career profile.",
        description=(
            "A capstone-style course where students choose a dataset, clean it, analyze "
            "it, visualize insights, and prepare a portfolio-ready project write-up."
        ),
        level=CourseLevel.INTERMEDIATE,
        tags=("portfolio", "capstone", "data-analysis", "career"),
        requirements=("SQL", "Python or spreadsheet analysis", "Visualization basics"),
        what_you_learn=(
            "Scope an analytics project",
            "Prepare a portfolio case study",
            "Explain analysis decisions",
            "Publish project evidence",
        ),
    ),
    CatalogCourse(
        title="Resume Preparation for Data Analysts",
        slug="resume-preparation-for-data-analysts",
        short_description="Position your skills, projects, and evidence for data analyst roles.",
        description=(
            "Students learn how to structure a data analyst resume, describe projects, "
            "show measurable outcomes, and align their profile with job descriptions."
        ),
        level=CourseLevel.BEGINNER,
        tags=("resume", "career", "data-analyst", "job-search"),
        requirements=("At least one project or learning milestone",),
        what_you_learn=(
            "Write data-focused resume bullets",
            "Show project evidence",
            "Match keywords responsibly",
            "Avoid common resume mistakes",
        ),
    ),
    CatalogCourse(
        title="Interview Preparation for Data Analysts",
        slug="interview-preparation-for-data-analysts",
        short_description="Practice technical, business, and behavioral analyst interviews.",
        description=(
            "A career readiness course covering SQL questions, analytics case prompts, "
            "project walkthroughs, stakeholder communication, and behavioral answers."
        ),
        level=CourseLevel.BEGINNER,
        tags=("interviews", "career", "data-analyst", "job-search"),
        requirements=("Basic SQL and analytics project experience",),
        what_you_learn=(
            "Answer common analyst interview questions",
            "Explain portfolio projects clearly",
            "Practice business case prompts",
            "Prepare concise behavioral answers",
        ),
    ),
)


TRACK_ATTACHMENTS: dict[str, tuple[TrackAttachment, ...]] = {
    "data-analyst": (
        TrackAttachment("excel-for-data-analysis", 10, TrackStage.FOUNDATION),
        TrackAttachment("sql-for-data-analysis", 20, TrackStage.FOUNDATION),
        TrackAttachment("python-fundamentals", 30, TrackStage.FOUNDATION),
        TrackAttachment("statistics-for-data-analysis", 40, TrackStage.FOUNDATION),
        TrackAttachment("python-for-data-analysis", 50, TrackStage.CORE),
        TrackAttachment("data-cleaning-and-preparation", 60, TrackStage.CORE),
        TrackAttachment("data-visualization-with-power-bi", 70, TrackStage.CORE),
        TrackAttachment("data-visualization-with-tableau", 80, TrackStage.CORE, False),
        TrackAttachment("business-intelligence-fundamentals", 90, TrackStage.CORE),
        TrackAttachment("data-analytics-portfolio-project", 100, TrackStage.ADVANCED),
        TrackAttachment("resume-preparation-for-data-analysts", 110, TrackStage.ADVANCED),
        TrackAttachment("interview-preparation-for-data-analysts", 120, TrackStage.ADVANCED),
    )
}


COURSES_BY_SLUG = {course.slug: course for course in DATA_ANALYST_COURSES}
