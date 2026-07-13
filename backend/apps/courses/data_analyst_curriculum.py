"""Review-required starter curriculum for the Data Analyst track.

The definitions here are intentionally content-only. They are used by a
production-safe management command and must not create learners, progress,
reviews, ratings, certificates, applications, or analytics.
"""

# ruff: noqa: E501

from __future__ import annotations

from dataclasses import dataclass

SOURCE = "production_data_analyst_curriculum"
CONTENT_STATUS = "review_required"


@dataclass(frozen=True)
class LessonDefinition:
    title: str
    objective: str
    example: str
    practice: str


@dataclass(frozen=True)
class ModuleDefinition:
    title: str
    order: int
    lessons: tuple[LessonDefinition, ...]


@dataclass(frozen=True)
class AssessmentDefinition:
    question_text: str
    options: tuple[str, str, str, str]
    correct_index: int
    explanation: str


@dataclass(frozen=True)
class CourseCurriculum:
    course_slug: str
    objectives: tuple[str, ...]
    prerequisites: tuple[str, ...]
    modules: tuple[ModuleDefinition, ...]
    assessments: tuple[AssessmentDefinition, ...]
    content_status: str = CONTENT_STATUS


def _lesson(title: str, objective: str, example: str, practice: str) -> LessonDefinition:
    return LessonDefinition(title=title, objective=objective, example=example, practice=practice)


def build_lesson_body(course_title: str, module_title: str, lesson: LessonDefinition) -> str:
    return "\n\n".join(
        [
            f"# {lesson.title}",
            f"## Measurable objective\n{lesson.objective}",
            (
                "## Short introduction\n"
                f"This review-required starter lesson belongs to **{course_title}** in the "
                f"module **{module_title}**. It introduces the concept and gives the "
                "instructor a structured base to expand before publishing."
            ),
            (
                "## Core explanation\n"
                "Focus on the analyst workflow: understand the question, inspect the data, "
                "choose the right technique, validate the result, and communicate the finding."
            ),
            f"## Example\n{lesson.example}",
            f"## Practice task\n{lesson.practice}",
            (
                "## Recap\n"
                "You should now be able to explain the concept, recognize when to use it, "
                "and complete a small practice task without relying on copied steps."
            ),
            "Content status: review_required.",
        ]
    )


def _assessment(topic: str) -> AssessmentDefinition:
    return AssessmentDefinition(
        question_text=f"Which habit best supports reliable work when practicing {topic}?",
        options=(
            "Document assumptions, validate outputs, and explain the result clearly.",
            "Skip validation when the output looks visually correct.",
            "Use only one tool for every analysis problem.",
            "Publish the first result before checking the source data.",
        ),
        correct_index=0,
        explanation=(
            "Reliable analysis requires documented assumptions, validation, and clear "
            "communication before results are used for decisions."
        ),
    )


CURRICULA: dict[str, CourseCurriculum] = {
    "excel-for-data-analysis": CourseCurriculum(
        course_slug="excel-for-data-analysis",
        objectives=(
            "Clean spreadsheet data for analysis.",
            "Use formulas, pivots, charts, and dashboards to answer business questions.",
        ),
        prerequisites=("Basic computer literacy",),
        modules=(
            ModuleDefinition(
                "Excel Foundations",
                1,
                (
                    _lesson("Excel foundations", "Navigate workbooks and structure analysis sheets.", "Create a workbook with raw data, calculations, and report tabs.", "Organize a small sales dataset into a clean workbook."),
                    _lesson("Data types and formatting", "Identify numbers, dates, text, and formatting issues.", "Convert text-formatted dates into real date values.", "Audit a column for inconsistent formats."),
                    _lesson("Formulas and functions", "Use formulas to calculate analyst-friendly metrics.", "Calculate revenue, margin, and conversion rate.", "Add formulas for three business metrics."),
                ),
            ),
            ModuleDefinition(
                "Analysis Workflow",
                2,
                (
                    _lesson("Sorting and filtering", "Filter datasets to isolate relevant records.", "Find late orders in a regional sales table.", "Filter a dataset by region, date, and status."),
                    _lesson("Data cleaning", "Fix common spreadsheet quality issues.", "Remove duplicate customer rows and standardize casing.", "Clean five messy fields in a sample dataset."),
                    _lesson("Lookup functions", "Use lookup functions to enrich analysis tables.", "Match product categories into a transactions sheet.", "Join reference data into an analysis table."),
                    _lesson("Pivot tables", "Summarize data with pivot tables.", "Create sales by month and category.", "Build two pivots from one dataset."),
                ),
            ),
            ModuleDefinition(
                "Reporting",
                3,
                (
                    _lesson("Charts", "Choose charts that fit the analytical question.", "Use a line chart for trends and a bar chart for comparisons.", "Create charts for trend, ranking, and composition."),
                    _lesson("Dashboard design", "Design a readable dashboard for stakeholders.", "Combine KPIs, trend charts, and filters on one page.", "Sketch a dashboard layout before building."),
                    _lesson("Final dashboard project", "Build a small dashboard and explain the insights.", "Summarize sales performance and recommend one action.", "Create a dashboard and write three insights."),
                ),
            ),
        ),
        assessments=(_assessment("Excel formulas"), _assessment("dashboard validation")),
    ),
    "sql-for-data-analysis": CourseCurriculum(
        "sql-for-data-analysis",
        ("Query relational data with SQL.", "Use joins, aggregations, and windows for analysis."),
        ("Comfort with tables and basic data terms",),
        (
            ModuleDefinition("SQL Foundations", 1, (
                _lesson("Relational concepts", "Explain tables, rows, columns, keys, and relationships.", "Connect customers to orders with a customer_id key.", "Draw a two-table relationship diagram."),
                _lesson("SELECT", "Retrieve specific columns from a table.", "Select customer name, city, and signup date.", "Write three simple SELECT queries."),
                _lesson("Filtering", "Use WHERE to narrow query results.", "Find orders above a threshold in one region.", "Filter by date, category, and numeric range."),
                _lesson("Sorting", "Use ORDER BY to rank query results.", "List highest revenue products first.", "Sort a query by two fields."),
            )),
            ModuleDefinition("Aggregation", 2, (
                _lesson("Aggregate functions", "Calculate counts, sums, averages, minimums, and maximums.", "Calculate monthly revenue.", "Write five aggregate queries."),
                _lesson("GROUP BY", "Summarize records by category or period.", "Group sales by region.", "Group a dataset by two dimensions."),
                _lesson("HAVING", "Filter grouped results correctly.", "Find categories with more than 100 orders.", "Write a grouped query with HAVING."),
            )),
            ModuleDefinition("Analytical SQL", 3, (
                _lesson("Joins", "Combine related tables without duplicating meaning.", "Join orders to customers and products.", "Write inner and left joins."),
                _lesson("Subqueries", "Break complex questions into nested query steps.", "Find customers above average spend.", "Rewrite one query using a subquery."),
                _lesson("CASE", "Create conditional labels in SQL.", "Classify orders as low, medium, or high value.", "Build a customer segment field."),
                _lesson("Window functions", "Use window functions for rankings and running totals.", "Rank products by revenue within each category.", "Create a running monthly total."),
                _lesson("Final SQL analysis project", "Answer a business question with a sequence of SQL queries.", "Analyze retention or sales performance.", "Submit queries plus a short insight summary."),
            )),
        ),
        (_assessment("SQL filtering"), _assessment("joins and aggregation")),
    ),
    "python-fundamentals": CourseCurriculum(
        "python-fundamentals",
        ("Write readable beginner Python.", "Use control flow, collections, files, and modules."),
        ("No prior programming experience required",),
        (
            ModuleDefinition("Setup and Basics", 1, (
                _lesson("Setup", "Run Python code in a local or notebook environment.", "Execute a print statement and simple calculation.", "Set up and run your first script."),
                _lesson("Variables", "Store and reuse values with clear variable names.", "Store a user's name and score.", "Create variables for a simple report."),
                _lesson("Data types", "Distinguish strings, numbers, booleans, and None.", "Convert a string number before adding.", "Inspect five values and label their type."),
                _lesson("Operators", "Use arithmetic and comparison operators.", "Calculate percentage change.", "Write expressions for three metrics."),
            )),
            ModuleDefinition("Control Flow", 2, (
                _lesson("Conditions", "Use if statements to branch logic.", "Classify a score as pass or retry.", "Write conditions for simple validation."),
                _lesson("Loops", "Repeat work over sequences safely.", "Loop through monthly revenue values.", "Summarize values in a list."),
                _lesson("Functions", "Wrap reusable logic in functions.", "Create a function for conversion rate.", "Write two small metric functions."),
            )),
            ModuleDefinition("Collections and Projects", 3, (
                _lesson("Lists", "Store ordered collections and access items.", "Keep a list of product prices.", "Filter a list manually."),
                _lesson("Tuples", "Use tuples for fixed grouped values.", "Represent latitude and longitude.", "Create tuples for immutable records."),
                _lesson("Dictionaries", "Use key-value data structures.", "Store customer attributes.", "Build a dictionary summary."),
                _lesson("Sets", "Find unique values with sets.", "Find unique regions in a list.", "Remove duplicates from a sequence."),
                _lesson("Files", "Read and write simple text files.", "Read lines from a CSV-like file.", "Write a small output report."),
                _lesson("Exceptions", "Handle expected errors clearly.", "Catch invalid numeric input.", "Add error handling to a converter."),
                _lesson("Modules", "Import and organize reusable code.", "Use the math module.", "Move a helper function into a module."),
                _lesson("Beginner project", "Build a small Python program from requirements.", "Create a command-line grade summarizer.", "Submit code and a short explanation."),
            )),
        ),
        (_assessment("Python fundamentals"), _assessment("control flow")),
    ),
    "statistics-for-data-analysis": CourseCurriculum(
        "statistics-for-data-analysis",
        ("Interpret common statistical summaries.", "Communicate uncertainty responsibly."),
        ("Basic arithmetic",),
        (
            ModuleDefinition("Describing Data", 1, (
                _lesson("Descriptive statistics", "Summarize the center, spread, and shape of data.", "Describe order values with summary stats.", "Summarize a numeric column."),
                _lesson("Mean, median, mode", "Choose a suitable measure of center.", "Compare income mean and median.", "Calculate and interpret all three."),
                _lesson("Variance and standard deviation", "Explain variation in a dataset.", "Compare stable and volatile weekly sales.", "Compute and describe spread."),
            )),
            ModuleDefinition("Probability and Sampling", 2, (
                _lesson("Probability", "Reason about likelihood in analyst language.", "Estimate conversion probability.", "Write probability statements from counts."),
                _lesson("Distributions", "Recognize common distribution shapes.", "Compare normal and skewed data.", "Sketch and describe two distributions."),
                _lesson("Sampling", "Explain why samples can mislead.", "Compare biased and random survey samples.", "Evaluate a sampling method."),
                _lesson("Confidence intervals", "Interpret a confidence interval without overclaiming.", "Report a range around average order value.", "Write an interval interpretation."),
            )),
            ModuleDefinition("Inference", 3, (
                _lesson("Hypothesis testing", "Explain null hypotheses and p-values at a high level.", "Compare conversion before and after a change.", "State a test question carefully."),
                _lesson("Correlation", "Interpret correlation without claiming causation.", "Compare ad spend and revenue.", "Find risks in a correlation claim."),
                _lesson("Regression foundations", "Explain what a simple regression estimates.", "Model sales from traffic.", "Interpret slope in plain language."),
                _lesson("Statistical interpretation", "Translate statistical outputs for stakeholders.", "Explain uncertainty in a dashboard note.", "Rewrite a technical result for a manager."),
            )),
        ),
        (_assessment("descriptive statistics"), _assessment("statistical interpretation")),
    ),
}


def _simple_course(slug: str, title: str, topics: tuple[str, ...]) -> CourseCurriculum:
    lessons = tuple(
        _lesson(
            topic,
            f"Explain and apply {topic.lower()} in a practical data analyst workflow.",
            f"Use {topic.lower()} to improve a small analysis deliverable.",
            f"Complete a focused practice task for {topic.lower()} and write one insight.",
        )
        for topic in topics
    )
    midpoint = max(1, len(lessons) // 2)
    modules = (
        ModuleDefinition(f"{title} Foundations", 1, lessons[:midpoint]),
        ModuleDefinition(f"{title} Applied Practice", 2, lessons[midpoint:]),
    )
    return CourseCurriculum(
        slug,
        (f"Apply core {title.lower()} skills to data analyst work.", "Produce reviewable evidence of learning."),
        ("Completion of earlier Data Analyst track foundations or equivalent experience",),
        modules,
        (_assessment(title), _assessment(f"{title} project work")),
    )


CURRICULA.update(
    {
        "python-for-data-analysis": _simple_course(
            "python-for-data-analysis",
            "Python for Data Analysis",
            ("NumPy", "Pandas", "Loading datasets", "Selecting and filtering", "Missing values", "Cleaning", "Grouping", "Aggregation", "Merging", "Dates", "Exploratory analysis", "Matplotlib", "Final analysis project"),
        ),
        "data-cleaning-and-preparation": _simple_course(
            "data-cleaning-and-preparation",
            "Data Cleaning and Preparation",
            ("Data quality", "Missing data", "Duplicates", "Types", "Outliers", "Text cleaning", "Date cleaning", "Validation", "Mapping", "Transformation", "Reproducible workflows", "Final cleaning project"),
        ),
        "data-visualization-with-power-bi": _simple_course(
            "data-visualization-with-power-bi",
            "Power BI",
            ("Setup", "Power Query", "Data modeling", "Relationships", "DAX", "Measures", "Visual selection", "Dashboard layout", "Filters and slicers", "Publishing foundation", "Final dashboard project"),
        ),
        "data-visualization-with-tableau": _simple_course(
            "data-visualization-with-tableau",
            "Tableau",
            ("Tableau interface", "Data connections", "Dimensions and measures", "Calculated fields", "Charts", "Filters", "Parameters", "Dashboards", "Stories", "Final visualization project"),
        ),
        "business-intelligence-fundamentals": _simple_course(
            "business-intelligence-fundamentals",
            "Business Intelligence Fundamentals",
            ("BI concepts", "KPIs", "Business requirements", "Data sources", "Models", "Dashboards", "Reporting", "Stakeholder communication", "Governance", "BI case study"),
        ),
        "data-analytics-portfolio-project": _simple_course(
            "data-analytics-portfolio-project",
            "Data Analytics Portfolio Project",
            ("Problem selection", "Dataset selection", "Problem statement", "Cleaning", "Exploration", "Analysis", "Visualization", "Recommendations", "Documentation", "GitHub presentation", "Portfolio presentation", "Submission checklist"),
        ),
        "resume-preparation-for-data-analysts": _simple_course(
            "resume-preparation-for-data-analysts",
            "Resume Preparation for Data Analysts",
            ("Resume structure", "Summary", "Skills", "Projects", "Experience bullets", "Action verbs", "Quantified achievements", "ATS keywords", "Tailoring", "Final checklist"),
        ),
        "interview-preparation-for-data-analysts": _simple_course(
            "interview-preparation-for-data-analysts",
            "Interview Preparation for Data Analysts",
            ("Interview process", "Behavioral questions", "Excel questions", "SQL questions", "Python questions", "Statistics questions", "Case studies", "Portfolio presentation", "STAR method", "Mock interview preparation"),
        ),
    }
)
