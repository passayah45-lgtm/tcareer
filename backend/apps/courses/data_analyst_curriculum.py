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
    explanation: str = ""
    common_mistakes: tuple[str, ...] = ()
    guided_practice: str = ""
    independent_practice: str = ""
    expected_output: str = ""
    validation_checklist: tuple[str, ...] = ()
    version_note: str = ""


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
    question_type: str = "multiple_choice"
    lesson_mapping: str = ""
    difficulty: str = "beginner"
    review_status: str = "review_required"
    is_certificate_eligible: bool = False


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
    if lesson.explanation:
        return "\n\n".join(
            [
                f"# {lesson.title}",
                f"## Measurable objective\n{lesson.objective}",
                (
                    "## Clear introduction\n"
                    f"This lesson is part of **{course_title}** / **{module_title}**. "
                    "It teaches one practical Excel skill and shows how to verify the result before using it in a report."
                ),
                f"## Excel-specific explanation\n{lesson.explanation}",
                f"## Worked example\n{lesson.example}",
                "## Common mistakes\n" + "\n".join(f"- {item}" for item in lesson.common_mistakes),
                f"## Guided practice\n{lesson.guided_practice}",
                f"## Independent practice\n{lesson.independent_practice}",
                f"## Expected output\n{lesson.expected_output}",
                "## Validation checklist\n" + "\n".join(f"- {item}" for item in lesson.validation_checklist),
                f"## Version note\n{lesson.version_note}",
                (
                    "## Recap\n"
                    f"{lesson.practice} Before moving on, save your workbook and write one sentence explaining what changed and how you checked it."
                ),
            ]
        )
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


def _excel_lesson(
    title: str,
    objective: str,
    explanation: str,
    example: str,
    guided: str,
    independent: str,
    expected: str,
    mistakes: tuple[str, ...],
    checklist: tuple[str, ...],
    version: str = "Microsoft Excel desktop and Excel Online both support this lesson. Menu names may vary slightly by version.",
) -> LessonDefinition:
    return LessonDefinition(
        title=title,
        objective=objective,
        example=example,
        practice=independent,
        explanation=explanation,
        common_mistakes=mistakes,
        guided_practice=guided,
        independent_practice=independent,
        expected_output=expected,
        validation_checklist=checklist,
        version_note=version,
    )


def _excel_question(
    prompt: str,
    options: tuple[str, str, str, str],
    correct_index: int,
    explanation: str,
    lesson: str,
    question_type: str = "multiple_choice",
    difficulty: str = "beginner",
) -> AssessmentDefinition:
    return AssessmentDefinition(
        question_text=prompt,
        options=options,
        correct_index=correct_index,
        explanation=explanation,
        question_type=question_type,
        lesson_mapping=lesson,
        difficulty=difficulty,
        review_status="review_required",
        is_certificate_eligible=False,
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
                    _excel_lesson(
                        "Excel foundations",
                        "Create a well-organized workbook with correctly named worksheets, basic data entry, and safe file organization.",
                        "An Excel workbook is the file you save. A worksheet is one tab inside that file. Rows run horizontally, columns run vertically, and a cell is one row-column intersection such as B4. A range is a group of cells such as A1:E20. The formula bar shows or edits the active cell contents, the name box shows the active cell address or named range, and the ribbon contains commands. For analysis work, keep raw data separate from calculations, dashboards, and notes so the original source can be checked later.",
                        "Create `Excel_Retail_Analysis_Practice.xlsx` with tabs named `Raw_Data`, `Clean_Data`, `Analysis`, `Pivot_Tables`, `Dashboard`, and `Notes`. Enter five sample sales rows on `Raw_Data` with headers for order date, region, product, units, unit price, discount, revenue, and profit.",
                        "Open a blank workbook, rename Sheet1 to `Raw_Data`, add the remaining tabs, freeze the header row on `Raw_Data`, and save the file in a course practice folder.",
                        "Using `excel_retail_sales_sample.csv`, import or paste the data into `Raw_Data`, then copy it into `Clean_Data` without changing the original tab.",
                        "A correctly named workbook with structured worksheets and sample sales data, where raw data is preserved separately from analysis work.",
                        ("Typing calculations directly into the raw data without keeping a backup.", "Leaving tabs named Sheet1/Sheet2 so reviewers cannot understand the workbook.", "Mixing notes, pivots, and raw records on the same sheet."),
                        ("Workbook has the required six tabs.", "`Raw_Data` contains headers and sample records.", "File is saved with a descriptive name.", "Raw data is not overwritten by calculations."),
                    ),
                    _excel_lesson(
                        "Data types and formatting",
                        "Identify text, numbers, dates, percentages, currency, and logical values, then apply formats without changing the underlying meaning.",
                        "Excel stores values separately from how they are displayed. A number can be formatted as currency or percentage, but it remains numeric. IDs and phone numbers should usually be stored as text so leading zeros are preserved. Dates can be ambiguous: `01/02/2026` may mean January 2 or February 1 depending on locale. Formatting improves readability, but analysis depends on the underlying value being correct.",
                        "Format `0.15` as `15%`, format `1250` as currency, store product code `00142` as text, and convert a text date column into real dates after confirming the intended locale.",
                        "In `Clean_Data`, inspect order dates, discounts, unit prices, and order IDs. Mark which columns should be date, number, percentage, currency, or text.",
                        "Find at least three formatting problems in the dataset, fix them, and write the fix in the `Notes` tab.",
                        "A cleaned worksheet where dates sort chronologically, percentages calculate correctly, currency is formatted for readability, and IDs keep leading zeros.",
                        ("Assuming every date format means the same thing in every country.", "Formatting a text number to look numeric without converting it.", "Converting IDs or phone numbers to numbers and losing leading zeros."),
                        ("Date values sort from oldest to newest correctly.", "Discounts behave as percentages in formulas.", "Currency columns remain numeric.", "Text identifiers preserve leading zeros."),
                        "Excel desktop has more import controls than Excel Online. If date parsing is ambiguous, confirm the source format before conversion.",
                    ),
                    _excel_lesson(
                        "Formulas and functions",
                        "Write formulas with relative, absolute, and mixed references using common functions for analyst metrics.",
                        "Formulas begin with `=` and can use operators such as `+`, `-`, `*`, `/`, and parentheses. Relative references such as `C2` move when copied. Absolute references such as `$B$1` stay fixed. Mixed references such as `$B2` or `B$1` lock only one direction. Analysts use functions like SUM, AVERAGE, MIN, MAX, COUNT, COUNTA, IF, and IFERROR to calculate and validate metrics.",
                        "`=SUM(E2:E20)` adds values from E2 through E20. `=$B$1*C2` multiplies C2 by a fixed value in B1. `=IF(D2>=1000,\"High\",\"Standard\")` labels large orders. `=IFERROR(G2/H2,0)` avoids an error when the denominator is blank or zero.",
                        "Calculate revenue as units multiplied by unit price after discount. Add an IF label for high-value orders.",
                        "Add formulas for revenue, cost, profit, profit margin, and high-value flag in `Clean_Data`.",
                        "Formula columns calculate consistent business metrics and can be copied down without breaking references.",
                        ("Forgetting `=` at the start of a formula.", "Copying a formula that should use an absolute reference but uses a relative reference.", "Hiding errors with IFERROR without checking why the error happened."),
                        ("Revenue equals units times unit price after discount.", "Absolute references remain fixed when copied.", "COUNT and COUNTA are used appropriately.", "IF labels match the defined threshold."),
                    ),
                ),
            ),
            ModuleDefinition(
                "Analysis Workflow",
                2,
                (
                    _excel_lesson(
                        "Sorting and filtering",
                        "Sort and filter complete sales records without breaking row integrity.",
                        "Sorting changes row order. Filtering hides rows temporarily. Always select the full data range or use an Excel Table before sorting, otherwise one column can move without the rest of the row. Use single-column sorting for simple lists and multi-level sorting for business questions like region first, then profit descending. Filters can search text, compare numbers, and limit dates.",
                        "Filter sales records to West region orders in Q1, then sort by profit from highest to lowest while preserving every complete row.",
                        "Turn `Clean_Data` into a table, filter by one region, use a date filter for one month, then clear the filters.",
                        "Create a filtered view for late or low-profit orders and write two observations in `Notes`.",
                        "Filtered records answer a specific business question without corrupting row relationships.",
                        ("Sorting only one selected column in a multi-column dataset.", "Forgetting a filter is active and thinking rows disappeared.", "Filtering formatted text dates instead of real date values."),
                        ("All columns remain aligned after sorting.", "Filters can be cleared.", "Numeric/date/text filters are used on appropriate data types.", "The result answers the stated scenario."),
                    ),
                    _excel_lesson(
                        "Data cleaning",
                        "Apply a reproducible checklist to fix common spreadsheet quality issues.",
                        "Cleaning prepares data for reliable analysis. Common issues include duplicates, blanks, inconsistent casing, extra spaces, invalid categories, incorrect formats, and blank rows. Excel tools include Remove Duplicates, Find and Replace, Text to Columns, Data Validation, and formulas such as TRIM, CLEAN, UPPER, LOWER, and PROPER. Keep a record of every cleaning step in `Notes`.",
                        "Use `=TRIM(PROPER(C2))` to remove extra spaces and standardize city names. Use Remove Duplicates on order ID only after confirming what makes a row duplicate.",
                        "Create a cleaning checklist: backup raw data, inspect columns, standardize text, convert types, handle blanks, validate categories, remove confirmed duplicates, document changes.",
                        "Clean the synthetic dataset: fix region casing, trim city/product names, resolve blank discounts, flag missing categories, and remove confirmed duplicate rows.",
                        "A `Clean_Data` tab with documented cleaning steps and values ready for formulas, pivots, and charts.",
                        ("Deleting rows with missing values without checking business meaning.", "Removing duplicates across all columns when only order ID should be unique.", "Changing raw data without preserving a copy."),
                        ("Raw data is unchanged.", "Cleaning decisions are documented.", "Duplicates are handled by a defined key.", "Invalid categories are flagged or corrected."),
                    ),
                    _excel_lesson(
                        "Lookup functions",
                        "Use lookup functions to enrich transaction data and handle missing matches responsibly.",
                        "Lookup functions bring information from one table into another. XLOOKUP can search left or right, return custom missing-value text, and defaults to exact match. VLOOKUP is common in older workbooks but searches from left to right and needs a column index. INDEX and MATCH provide a flexible foundation when XLOOKUP is unavailable. Approximate match is useful for ranges, but exact match is safer for IDs and categories.",
                        "`=XLOOKUP(F2,Products[Product],Products[Category],\"Missing\",0)` returns a category for the product in F2. Older Excel may use `=VLOOKUP(F2,Products!A:C,3,FALSE)`.",
                        "Build a small product reference table and use XLOOKUP to fill missing categories in `Clean_Data`.",
                        "Add a lookup status column that flags products with no match, then count missing matches.",
                        "Transactions are enriched from a reference table, and missing lookup values are visible instead of silently ignored.",
                        ("Using approximate match when exact match is required.", "Assuming VLOOKUP can search to the left.", "Not checking missing lookup results.", "Hard-coding column numbers without documenting them."),
                        ("Lookup uses exact match for product IDs/names.", "Missing values return a clear label.", "Version-compatible alternative is documented.", "Lookup results are spot-checked."),
                        "XLOOKUP is available in Microsoft 365 and newer Excel versions. Use VLOOKUP or INDEX/MATCH when working in older Excel versions.",
                    ),
                    _excel_lesson(
                        "Pivot tables",
                        "Create and refresh pivot tables that summarize clean sales data by business dimensions.",
                        "Pivot tables summarize records without writing many formulas. Good source data has one header row, no merged cells, no blank columns, and consistent data types. Rows and columns define categories, Values define calculations, and Filters limit the view. Check whether Excel is summarizing by Sum or Count. Refresh the pivot after source data changes and expand the source range or use an Excel Table.",
                        "Create a pivot showing total revenue and profit by region and month. Group dates by month, sort regions by profit, and add category as a filter.",
                        "Build one pivot for revenue by region and another for profit by category.",
                        "Create a pivot-table summary that identifies the top region, top category, and lowest-margin category.",
                        "At least two pivot tables summarize sales and profit accurately from the cleaned dataset.",
                        ("Building pivots from messy or partially selected data.", "Leaving Values as Count when Sum is intended.", "Forgetting to refresh after changing data.", "Using a fixed range that excludes new rows."),
                        ("Source data is clean and table-based.", "Values summarize by the intended calculation.", "Dates group correctly.", "Pivot is refreshed after source edits."),
                    ),
                ),
            ),
            ModuleDefinition(
                "Reporting",
                3,
                (
                    _excel_lesson(
                        "Charts",
                        "Choose chart types that match the analytical question and avoid misleading visual design.",
                        "Column and bar charts compare categories. Line charts show trends over time. Pie charts are limited and should only be used for a small number of parts of a whole. Scatter plots show relationships between two numeric measures. Combo charts can compare metrics with different scales, but they need clear axes. Good charts have titles, readable axes, useful labels, accessible colors, and honest scales.",
                        "Use a line chart for monthly revenue trends, a bar chart for profit by category, and avoid a pie chart when there are many product categories.",
                        "Create three charts from pivot tables: trend, ranking, and category comparison.",
                        "Explain why each chart type was selected and identify one chart type you rejected.",
                        "Three readable charts that answer three different business questions without misleading scales.",
                        ("Using pie charts for too many categories.", "Starting a bar chart axis at a misleading value.", "Using colors that are hard to distinguish.", "Adding labels that clutter the chart."),
                        ("Chart type matches the question.", "Title states the metric and period.", "Axes and legends are readable.", "Color use is consistent and accessible."),
                    ),
                    _excel_lesson(
                        "Dashboard design",
                        "Design a one-page dashboard that communicates KPIs, trends, and recommendations to a business audience.",
                        "A dashboard should answer a specific audience question. Start by defining KPIs such as revenue, profit, order count, average order value, and margin. Use visual hierarchy: most important numbers first, trends next, details last. Keep layout consistent, leave whitespace, use filters or slicers where supported, and avoid clutter. Accessibility matters: use sufficient contrast and do not rely on color alone.",
                        "Sketch a dashboard with KPI cards at the top, monthly trend on the left, category profit on the right, and notes/recommendations at the bottom.",
                        "Create a one-page dashboard layout sketch before building anything in Excel.",
                        "Build a dashboard using your pivots and charts, then write what decision the dashboard supports.",
                        "A one-page dashboard plan and draft dashboard that is readable, purposeful, and aligned with stakeholder questions.",
                        ("Adding every chart instead of selecting the useful ones.", "Using inconsistent colors or number formats.", "Forgetting to define the audience.", "Making slicers or filters unclear."),
                        ("Dashboard has a stated audience and purpose.", "KPIs are defined.", "Layout uses hierarchy and whitespace.", "Insights are visible without scrolling."),
                    ),
                    _excel_lesson(
                        "Final dashboard project",
                        "Complete an end-to-end retail sales analysis workbook and explain business recommendations.",
                        "The final project uses the original synthetic dataset `excel_retail_sales_sample.csv`. Required tabs are `Raw_Data`, `Clean_Data`, `Analysis`, `Pivot_Tables`, `Dashboard`, and `Notes`. Learners must inspect the dataset, clean relevant fields, calculate revenue/cost/profit, summarize metrics, build pivot tables, choose charts, assemble a dashboard, explain findings, and provide business recommendations.",
                        "Analyze retail sales performance by region, product category, month, and customer segment. Recommend where the business should focus next month.",
                        "Import the dataset into `Raw_Data`, create `Clean_Data`, calculate revenue and profit, then build KPI formulas for revenue, profit, orders, average order value, and margin.",
                        "Submit a workbook with cleaned data, at least two pivot tables, at least three charts, a dashboard, three written insights, and three business recommendations.",
                        "A complete workbook with required tabs, calculations, pivots, charts, dashboard, notes, and recommendations. The visual design may vary, but the analysis must be reproducible.",
                        ("Submitting a dashboard without documenting cleaning steps.", "Using charts that do not match the question.", "Changing raw data directly.", "Writing recommendations that do not follow from the numbers."),
                        ("All required tabs exist.", "Cleaning issues are documented.", "Revenue and profit formulas are correct.", "Dashboard includes KPIs, pivots/charts, insights, and recommendations.", "Workbook can be reviewed without a private external file."),
                    ),
                ),
            ),
        ),
        assessments=(
            _excel_question("What is the difference between a workbook and a worksheet?", ("A workbook is the saved Excel file; a worksheet is one tab inside it.", "A worksheet is the saved Excel file; a workbook is one cell.", "They mean exactly the same thing.", "A workbook is only used for formulas."), 0, "A workbook can contain many worksheets.", "Excel foundations"),
            _excel_question("Which cell reference stays fixed when copied from one row to another?", ("B2", "$B$2", "B$2 only when copied across columns", "Sheet1!B2 always changes to text"), 1, "`$B$2` is an absolute reference and stays fixed when copied.", "Formulas and functions"),
            _excel_question("Why should order IDs usually be stored as text?", ("Text preserves leading zeros and avoids numeric formatting changes.", "Text makes formulas faster.", "Text automatically removes duplicates.", "Text is required for pivot tables."), 0, "IDs are labels, not quantities; storing them as text preserves their exact form.", "Data types and formatting"),
            _excel_question("What is the safest first step before cleaning a worksheet?", ("Delete blank rows immediately.", "Preserve or copy the raw data before editing.", "Create a pie chart.", "Sort one column only."), 1, "Keeping raw data unchanged protects auditability and rollback.", "Data cleaning"),
            _excel_question("Which function is best for removing extra spaces around text?", ("TRIM", "COUNT", "MAX", "IFERROR"), 0, "TRIM removes leading, trailing, and repeated extra spaces between words.", "Data cleaning"),
            _excel_question("When is XLOOKUP usually safer than VLOOKUP?", ("When you need exact match, custom missing-value handling, or lookup to the left.", "Only when creating charts.", "Only for percentages.", "When the data has no headers."), 0, "XLOOKUP is more flexible and defaults to exact match behavior.", "Lookup functions"),
            _excel_question("What should you check if a pivot table shows Count instead of Sum?", ("The field may be text or contain blanks/non-numeric values.", "The workbook is always corrupted.", "The chart type is wrong.", "The worksheet name is too long."), 0, "Excel often counts fields that are text or mixed type.", "Pivot tables"),
            _excel_question("Which chart is usually best for monthly sales trends?", ("Line chart", "Pie chart", "Single KPI card", "Scatter plot with no date axis"), 0, "A line chart is usually best for showing change over time.", "Charts", "chart_selection"),
            _excel_question("Which dashboard practice improves readability?", ("Use every chart available.", "Put the most important KPIs first and keep formatting consistent.", "Hide all labels.", "Use random colors for each visual."), 1, "A dashboard should use hierarchy, consistency, and clear labeling.", "Dashboard design"),
            _excel_question("What does `=IF(D2>=1000,\"High\",\"Standard\")` return when D2 is 1250?", ("High", "Standard", "FALSE", "#VALUE!"), 0, "1250 is greater than or equal to 1000, so the formula returns High.", "Formulas and functions", "applied_formula"),
            _excel_question("What does `=SUM(E2:E20)` calculate?", ("The total of values from E2 through E20.", "The average of E2 and E20 only.", "The number of text cells in E2:E20.", "The largest value in E2:E20."), 0, "SUM adds every numeric value in the specified range.", "Formulas and functions", "applied_formula"),
            _excel_question("Why use `=IFERROR(G2/H2,0)` carefully?", ("It can hide a real data-quality problem if you do not investigate the original error.", "It permanently deletes the formula.", "It only works in charts.", "It changes dates to text."), 0, "IFERROR is useful, but analysts should still understand why an error happened.", "Formulas and functions", "applied_formula"),
            _excel_question("If a tax rate is stored in B1 and copied down a column, which formula correctly locks B1?", ("=B1*C2", "=$B$1*C2", "=B$1*$C$2 for every row only", "=LOCK(B1)*C2"), 1, "Absolute references lock the tax-rate cell while the row value changes.", "Formulas and functions", "applied_formula"),
            _excel_question("A region column contains `west`, ` West `, and `WEST`. What cleaning approach is appropriate?", ("Trim spaces and standardize casing before analysis.", "Delete the whole region column.", "Treat all three as separate official regions.", "Convert the values to currency."), 0, "Whitespace and casing should be standardized to avoid split categories.", "Data cleaning", "data_cleaning_scenario"),
            _excel_question("A discount column has blank cells. What should an analyst do first?", ("Decide and document whether blank means zero, unknown, or missing before filling values.", "Replace every blank in the workbook with 100%.", "Delete every row with a blank discount.", "Convert the column to text."), 0, "Missing-value handling depends on business meaning and must be documented.", "Data cleaning", "data_cleaning_scenario"),
            _excel_question("You find duplicate order IDs with identical values in all fields. What is the safest action?", ("Confirm the duplicate rule, remove one duplicate in Clean_Data, and document the change.", "Delete all records with that order ID.", "Ignore duplicates because pivot tables fix them.", "Change the order IDs randomly."), 0, "Duplicates should be handled using a defined key and documented cleaning step.", "Data cleaning", "data_cleaning_scenario"),
            _excel_question("A pivot table shows revenue by month, but newly added rows are missing. What should you do?", ("Refresh the pivot and confirm the source range/table includes the new rows.", "Reinstall Excel.", "Change every date to text.", "Delete the pivot filters only."), 0, "Pivots do not always update until refreshed, and fixed ranges may exclude new rows.", "Pivot tables", "pivot_interpretation"),
            _excel_question("A pivot value field is counting orders when you need total revenue. What should you change?", ("Value Field Settings from Count to Sum, after checking the source field is numeric.", "The worksheet tab color.", "The legend position.", "The workbook password."), 0, "The summary function controls whether a field is counted or summed.", "Pivot tables", "pivot_interpretation"),
            _excel_question("Which chart best compares profit across product categories?", ("Horizontal bar chart", "Pie chart with 20 slices", "Line chart with categories as dates", "Scatter plot with no numeric x-axis"), 0, "Bar charts are effective for comparing categories.", "Charts", "chart_selection"),
            _excel_question("Which chart is risky when showing many categories with small differences?", ("Pie chart", "Bar chart", "Line chart", "Column chart"), 0, "Pie charts become hard to read with many categories or small differences.", "Charts", "chart_selection"),
            _excel_question("What must the final project `Notes` tab include?", ("Cleaning decisions, assumptions, insights, and business recommendations.", "Only copied chart images.", "Passwords for protected sheets.", "A list of private customer names."), 0, "The Notes tab makes the analysis reviewable and explains decisions.", "Final dashboard project"),
            _excel_question("Which workbook tab should preserve the original imported records?", ("Raw_Data", "Dashboard", "Notes", "Pivot_Tables"), 0, "Raw_Data should preserve the original source records.", "Final dashboard project"),
            _excel_question("What makes a final dashboard recommendation credible?", ("It is supported by the cleaned data, calculations, pivots, and charts.", "It sounds confident even without data.", "It uses the brightest color.", "It ignores low-performing categories."), 0, "Recommendations must follow from the analysis evidence.", "Final dashboard project"),
        ),
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
