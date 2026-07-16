"""
Management command to seed T-Career with realistic demo data.

Usage:
    python manage.py seed_demo_data
    python manage.py seed_demo_data --clear   # clears existing data first

Creates:
    - 5 instructor accounts
    - 20 courses across all career tracks
    - 50 student accounts
    - Enrollments and progress records
"""

import random
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.users.models import User, UserRole
from apps.courses.models import (
    Course,
    Lesson,
    Enrollment,
    LessonProgress,
    CourseStatus,
    LessonType,
    EnrollmentStatus,
)


INSTRUCTORS = [
    {
        "email": "sarah.chen@tcareer.demo",
        "full_name": "Sarah Chen",
        "bio": "Senior Python Engineer with 8 years at fintech companies.",
    },
    {
        "email": "james.okafor@tcareer.demo",
        "full_name": "James Okafor",
        "bio": "Full Stack Developer and open source contributor.",
    },
    {
        "email": "priya.sharma@tcareer.demo",
        "full_name": "Priya Sharma",
        "bio": "Data Scientist with experience at e-commerce platforms.",
    },
    {
        "email": "carlos.mendez@tcareer.demo",
        "full_name": "Carlos Mendez",
        "bio": "DevOps Engineer specialising in Kubernetes and AWS.",
    },
    {
        "email": "aiko.tanaka@tcareer.demo",
        "full_name": "Aiko Tanaka",
        "bio": "UI/UX Designer and Figma expert.",
    },
]

COURSES = [
    {
        "title": "Python Fundamentals for Absolute Beginners",
        "short_description": "Learn Python from scratch with hands-on projects.",
        "description": "A practical introduction to Python programming covering variables, data types, control flow, functions, and file handling. Every concept is reinforced with a real project.",
        "level": "beginner",
        "price": "0.00",
        "tags": ["python", "programming", "beginner"],
        "what_you_learn": [
            "Write Python scripts from scratch",
            "Understand core data structures",
            "Build simple command-line programs",
            "Read and write files",
        ],
        "instructor_index": 0,
        "lesson_count": 12,
    },
    {
        "title": "JavaScript Essentials",
        "short_description": "The complete foundation for web development.",
        "description": "Covers JavaScript syntax, DOM manipulation, events, asynchronous programming, and the fetch API. Build real projects in every section.",
        "level": "beginner",
        "price": "0.00",
        "tags": ["javascript", "web", "programming"],
        "what_you_learn": [
            "Write modern JavaScript",
            "Manipulate the browser DOM",
            "Handle user events",
            "Fetch data from APIs",
        ],
        "instructor_index": 1,
        "lesson_count": 14,
    },
    {
        "title": "React from Zero to First App",
        "short_description": "Build modern user interfaces with React.",
        "description": "Covers components, props, state, hooks, and connecting to an API. Build a complete application by the end of the course.",
        "level": "intermediate",
        "price": "19.00",
        "tags": ["react", "javascript", "frontend"],
        "what_you_learn": [
            "Build component trees",
            "Manage state with hooks",
            "Fetch and display API data",
            "Structure a React application",
        ],
        "instructor_index": 1,
        "lesson_count": 16,
    },
    {
        "title": "Python for Web Development with Django",
        "short_description": "Build a complete web application with Django.",
        "description": "Covers models, views, templates, forms, authentication, and REST API creation with Django REST Framework.",
        "level": "intermediate",
        "price": "19.00",
        "tags": ["python", "django", "backend", "api"],
        "what_you_learn": [
            "Build a Django application from scratch",
            "Design a database schema",
            "Create REST APIs",
            "Implement user authentication",
        ],
        "instructor_index": 0,
        "lesson_count": 18,
    },
    {
        "title": "Data Analysis with Python and Pandas",
        "short_description": "Analyse real datasets using Python and Pandas.",
        "description": "Covers data loading, cleaning, transformation, aggregation, and visualization with Matplotlib. Work with real-world datasets throughout.",
        "level": "intermediate",
        "price": "19.00",
        "tags": ["python", "pandas", "data", "analytics"],
        "what_you_learn": [
            "Load and clean datasets",
            "Perform groupby analysis",
            "Create charts with Matplotlib",
            "Handle missing data",
        ],
        "instructor_index": 2,
        "lesson_count": 13,
    },
    {
        "title": "SQL for Beginners",
        "short_description": "Master the language every data professional needs.",
        "description": "Covers SELECT queries, joins, aggregations, subqueries, and database design basics using PostgreSQL.",
        "level": "beginner",
        "price": "0.00",
        "tags": ["sql", "database", "data"],
        "what_you_learn": [
            "Write SELECT, INSERT, UPDATE, DELETE queries",
            "Join multiple tables",
            "Use aggregate functions",
            "Design a simple schema",
        ],
        "instructor_index": 2,
        "lesson_count": 11,
    },
    {
        "title": "Docker and Containerization from Scratch",
        "short_description": "Package and deploy applications using Docker.",
        "description": "Covers Dockerfiles, images, containers, volumes, networking, and Docker Compose for multi-service applications.",
        "level": "intermediate",
        "price": "19.00",
        "tags": ["docker", "devops", "containers"],
        "what_you_learn": [
            "Build Docker images",
            "Run containers",
            "Use Docker Compose",
            "Manage volumes and networks",
        ],
        "instructor_index": 3,
        "lesson_count": 10,
    },
    {
        "title": "AWS Cloud Fundamentals",
        "short_description": "Understand the core AWS services used in production.",
        "description": "Covers EC2, S3, RDS, Lambda, IAM, VPC, and CloudWatch. Deploy a real web application to AWS by the end of the course.",
        "level": "beginner",
        "price": "19.00",
        "tags": ["aws", "cloud", "devops"],
        "what_you_learn": [
            "Launch and configure AWS services",
            "Understand IAM permissions",
            "Deploy a web application to AWS",
            "Set up monitoring with CloudWatch",
        ],
        "instructor_index": 3,
        "lesson_count": 14,
    },
    {
        "title": "Machine Learning Fundamentals with Python",
        "short_description": "Understand machine learning and build your first models.",
        "description": "Covers supervised learning, model evaluation, and feature engineering using scikit-learn. Build classification and regression models on real datasets.",
        "level": "intermediate",
        "price": "29.00",
        "tags": ["machine learning", "python", "ai", "data science"],
        "what_you_learn": [
            "Train classification and regression models",
            "Evaluate model performance",
            "Preprocess features",
            "Avoid overfitting",
        ],
        "instructor_index": 2,
        "lesson_count": 15,
    },
    {
        "title": "Git and GitHub for Developers",
        "short_description": "Master version control and collaborative development.",
        "description": "Covers commits, branches, merges, pull requests, rebasing, and GitHub workflows. Required knowledge for every software development role.",
        "level": "beginner",
        "price": "0.00",
        "tags": ["git", "github", "version control"],
        "what_you_learn": [
            "Manage code with Git",
            "Collaborate via pull requests",
            "Resolve merge conflicts",
            "Use Git flow branching strategy",
        ],
        "instructor_index": 1,
        "lesson_count": 8,
    },
    {
        "title": "TypeScript for JavaScript Developers",
        "short_description": "Add type safety to your JavaScript code.",
        "description": "Covers TypeScript fundamentals, interfaces, generics, enums, and integration with React and Node.js.",
        "level": "intermediate",
        "price": "19.00",
        "tags": ["typescript", "javascript", "frontend"],
        "what_you_learn": [
            "Convert JavaScript to TypeScript",
            "Define interfaces and types",
            "Use generics",
            "Type React components",
        ],
        "instructor_index": 1,
        "lesson_count": 12,
    },
    {
        "title": "PostgreSQL for Developers",
        "short_description": "Use PostgreSQL effectively in your applications.",
        "description": "Covers schema design, indexing, query optimization, transactions, and JSON support. Learn to write queries that perform well at scale.",
        "level": "intermediate",
        "price": "19.00",
        "tags": ["postgresql", "sql", "database", "backend"],
        "what_you_learn": [
            "Design normalized schemas",
            "Write optimized queries",
            "Use indexes effectively",
            "Work with JSONB",
        ],
        "instructor_index": 2,
        "lesson_count": 12,
    },
    {
        "title": "UI/UX Design Fundamentals with Figma",
        "short_description": "Design interfaces that people actually want to use.",
        "description": "Covers design principles, wireframing, prototyping, user research basics, and Figma. Build a complete mobile app design by the end of the course.",
        "level": "beginner",
        "price": "19.00",
        "tags": ["design", "figma", "ux", "ui"],
        "what_you_learn": [
            "Apply visual design principles",
            "Create wireframes and prototypes in Figma",
            "Conduct basic user research",
            "Design a mobile app screen",
        ],
        "instructor_index": 4,
        "lesson_count": 11,
    },
    {
        "title": "Node.js and Express Backend Development",
        "short_description": "Build REST APIs with Node.js and Express.",
        "description": "Covers routing, middleware, authentication with JWT, database integration with PostgreSQL, and deployment to a cloud server.",
        "level": "intermediate",
        "price": "19.00",
        "tags": ["nodejs", "express", "backend", "javascript"],
        "what_you_learn": [
            "Build and deploy a REST API",
            "Implement JWT authentication",
            "Connect to a database",
            "Handle errors and validation",
        ],
        "instructor_index": 1,
        "lesson_count": 14,
    },
    {
        "title": "Cybersecurity Fundamentals",
        "short_description": "Understand how attacks work and how to defend against them.",
        "description": "Covers networking basics, OWASP Top 10, cryptography, authentication security, and secure coding practices for web applications.",
        "level": "beginner",
        "price": "19.00",
        "tags": ["security", "cybersecurity", "networking"],
        "what_you_learn": [
            "Identify common vulnerabilities",
            "Understand OWASP Top 10",
            "Implement secure authentication",
            "Use encryption correctly",
        ],
        "instructor_index": 3,
        "lesson_count": 12,
    },
    {
        "title": "Kotlin for Android Development",
        "short_description": "Build Android apps with Kotlin and Jetpack Compose.",
        "description": "Covers Kotlin syntax, Compose UI, navigation, state management, and REST API integration. Build a complete Android app during the course.",
        "level": "intermediate",
        "price": "29.00",
        "tags": ["kotlin", "android", "mobile"],
        "what_you_learn": [
            "Write Kotlin code",
            "Build UIs with Jetpack Compose",
            "Navigate between screens",
            "Call REST APIs from Android",
        ],
        "instructor_index": 0,
        "lesson_count": 17,
    },
    {
        "title": "Data Visualization with Python",
        "short_description": "Turn raw data into clear, compelling visuals.",
        "description": "Covers Matplotlib, Seaborn, and Plotly. Build interactive dashboards and publication-quality charts from real datasets.",
        "level": "intermediate",
        "price": "19.00",
        "tags": ["python", "data", "visualization", "analytics"],
        "what_you_learn": [
            "Create bar, line, scatter, and heatmap charts",
            "Customize visual styles",
            "Build interactive Plotly charts",
            "Export publication-quality figures",
        ],
        "instructor_index": 2,
        "lesson_count": 10,
    },
    {
        "title": "HTML and CSS from Zero",
        "short_description": "Build real web pages from scratch.",
        "description": "Covers HTML5 semantics, CSS layouts with Flexbox and Grid, responsive design, and accessibility basics. Build five real web pages during the course.",
        "level": "beginner",
        "price": "0.00",
        "tags": ["html", "css", "frontend", "web"],
        "what_you_learn": [
            "Write semantic HTML",
            "Build responsive layouts",
            "Use Flexbox and CSS Grid",
            "Apply accessibility standards",
        ],
        "instructor_index": 4,
        "lesson_count": 10,
    },
    {
        "title": "English for Tech Professionals",
        "short_description": "Communicate confidently in international tech environments.",
        "description": "Covers technical writing, email communication, code review language, meeting participation, and presentation skills for software developers.",
        "level": "beginner",
        "price": "19.00",
        "tags": ["english", "communication", "career", "language"],
        "what_you_learn": [
            "Write clear technical documentation",
            "Participate in English-language meetings",
            "Give technical presentations",
            "Communicate in code reviews",
        ],
        "instructor_index": 4,
        "lesson_count": 15,
    },
    {
        "title": "Product Management for Tech Professionals",
        "short_description": "Learn how products are built from idea to launch.",
        "description": "Covers user research, writing PRDs, prioritization frameworks, working with engineers, and measuring success with metrics.",
        "level": "beginner",
        "price": "19.00",
        "tags": ["product management", "business", "career"],
        "what_you_learn": [
            "Write a product requirements document",
            "Conduct user interviews",
            "Prioritize features using frameworks",
            "Define success metrics",
        ],
        "instructor_index": 0,
        "lesson_count": 13,
    },
]

LESSON_TITLES = {
    "Python Fundamentals for Absolute Beginners": [
        "Setting up Python and your first program",
        "Variables and data types",
        "Strings and string formatting",
        "Lists and list operations",
        "Dictionaries and sets",
        "Conditional statements",
        "Loops: for and while",
        "Functions and return values",
        "Modules and imports",
        "File reading and writing",
        "Error handling with try/except",
        "Final project: build a to-do list app",
    ],
    "default": [
        "Introduction and setup",
        "Core concepts part 1",
        "Core concepts part 2",
        "Hands-on practice",
        "Intermediate topics",
        "Building your first project",
        "Advanced patterns",
        "Testing your work",
        "Deployment and next steps",
        "Final project",
    ],
}


class Command(BaseCommand):
    help = "Seed the database with demo data for T-Career development and testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing demo data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing demo data...")
            User.objects.filter(email__endswith="@tcareer.demo").delete()
            User.objects.filter(email__endswith="@student.demo").delete()

        self.stdout.write("Creating instructors...")
        instructors = self._create_instructors()

        self.stdout.write("Creating courses and lessons...")
        courses = self._create_courses(instructors)

        self.stdout.write("Creating students...")
        students = self._create_students(50)

        self.stdout.write("Creating enrollments and progress...")
        self._create_enrollments(students, courses)

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDemo data created successfully:\n"
                f"  Instructors: {len(instructors)}\n"
                f"  Courses: {len(courses)}\n"
                f"  Students: {len(students)}\n"
            )
        )

    def _create_instructors(self):
        instructors = []
        for data in INSTRUCTORS:
            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults={
                    "full_name": data["full_name"],
                    "role": UserRole.INSTRUCTOR,
                    "is_verified": True,
                    "is_active": True,
                },
            )
            if created:
                user.set_password("DemoPass123!")
                user.save()
            instructors.append(user)
            status = "Created" if created else "Already exists"
            self.stdout.write(f"  {status}: {user.full_name}")
        return instructors

    def _create_courses(self, instructors):
        courses = []
        for course_data in COURSES:
            instructor = instructors[course_data["instructor_index"]]
            course, created = Course.objects.get_or_create(
                title=course_data["title"],
                defaults={
                    "instructor": instructor,
                    "short_description": course_data["short_description"],
                    "description": course_data["description"],
                    "level": course_data["level"],
                    "price": course_data["price"],
                    "status": CourseStatus.PUBLISHED,
                    "tags": course_data["tags"],
                    "what_you_learn": course_data["what_you_learn"],
                    "pass_threshold": 70,
                },
            )

            if created:
                lesson_titles = LESSON_TITLES.get(course_data["title"], LESSON_TITLES["default"])
                lesson_count = course_data["lesson_count"]

                for i in range(lesson_count):
                    title = lesson_titles[i] if i < len(lesson_titles) else f"Lesson {i + 1}"
                    Lesson.objects.create(
                        course=course,
                        title=title,
                        lesson_type=LessonType.VIDEO,
                        content=f"Lesson content for: {title}",
                        position=(i + 1) * 10,
                        is_published=True,
                        is_free_preview=(i == 0),
                    )

            courses.append(course)
            status = "Created" if created else "Already exists"
            self.stdout.write(f"  {status}: {course.title} ({course_data['lesson_count']} lessons)")

        return courses

    def _create_students(self, count):
        first_names = [
            "Alex",
            "Jordan",
            "Morgan",
            "Taylor",
            "Casey",
            "Riley",
            "Drew",
            "Avery",
            "Quinn",
            "Sage",
            "River",
            "Phoenix",
            "Kai",
            "Skylar",
            "Rowan",
            "Finley",
            "Blair",
            "Emery",
            "Reese",
            "Dakota",
            "Peyton",
            "Hayden",
            "Cameron",
            "Logan",
            "Jamie",
            "Jesse",
            "Dylan",
            "Robin",
            "Kendall",
            "Marley",
        ]
        last_names = [
            "Smith",
            "Johnson",
            "Williams",
            "Brown",
            "Jones",
            "Garcia",
            "Miller",
            "Davis",
            "Rodriguez",
            "Martinez",
            "Hernandez",
            "Lopez",
            "Gonzalez",
            "Wilson",
            "Anderson",
            "Thomas",
            "Taylor",
            "Moore",
            "Jackson",
            "Martin",
            "Lee",
            "Thompson",
            "White",
            "Harris",
            "Sanchez",
            "Clark",
            "Ramirez",
            "Lewis",
            "Robinson",
            "Walker",
            "Young",
            "Allen",
            "King",
            "Wright",
        ]

        students = []
        for i in range(count):
            first = random.choice(first_names)
            last = random.choice(last_names)
            email = f"student{i + 1}@student.demo"
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": f"{first} {last}",
                    "role": UserRole.STUDENT,
                    "is_verified": True,
                    "is_active": True,
                },
            )
            if created:
                user.set_password("DemoPass123!")
                user.save()
            students.append(user)

        self.stdout.write(f"  Created {len(students)} students")
        return students

    def _create_enrollments(self, students, courses):
        enrollment_count = 0
        progress_count = 0

        for student in students:
            enrolled_courses = random.sample(courses, random.randint(1, 4))

            for course in enrolled_courses:
                if Enrollment.objects.filter(user=student, course=course).exists():
                    continue

                enrollment = Enrollment.objects.create(
                    user=student,
                    course=course,
                    status=EnrollmentStatus.ACTIVE,
                    amount_paid=course.price,
                )
                enrollment_count += 1

                lessons = list(course.lessons.filter(is_published=True))
                if not lessons:
                    continue

                completed_count = random.randint(0, len(lessons))
                for j, lesson in enumerate(lessons):
                    if j < completed_count:
                        LessonProgress.objects.create(
                            enrollment=enrollment,
                            lesson=lesson,
                            is_completed=True,
                            watch_percentage=100,
                            last_position_seconds=random.randint(300, 3600),
                        )
                        progress_count += 1
                    elif j == completed_count:
                        LessonProgress.objects.create(
                            enrollment=enrollment,
                            lesson=lesson,
                            is_completed=False,
                            watch_percentage=random.randint(10, 80),
                            last_position_seconds=random.randint(60, 600),
                        )
                        progress_count += 1

        self.stdout.write(
            f"  Created {enrollment_count} enrollments and {progress_count} progress records"
        )


QUIZ_QUESTIONS = {
    "Python Fundamentals for Absolute Beginners": [
        {
            "question_text": "Which keyword is used to define a function in Python?",
            "options": ["func", "def", "function", "define"],
            "correct_index": 1,
            "explanation": "In Python, the 'def' keyword is used to define a function.",
            "position": 10,
        },
        {
            "question_text": "What is the correct way to create a list in Python?",
            "options": [
                "list = (1, 2, 3)",
                "list = {1, 2, 3}",
                "list = [1, 2, 3]",
                "list = <1, 2, 3>",
            ],
            "correct_index": 2,
            "explanation": "Lists in Python are created using square brackets [].",
            "position": 20,
        },
        {
            "question_text": "What does the len() function return?",
            "options": [
                "The last element",
                "The data type",
                "The number of items",
                "The memory size",
            ],
            "correct_index": 2,
            "explanation": "len() returns the number of items in an object like a list or string.",
            "position": 30,
        },
        {
            "question_text": "Which of these is NOT a valid Python data type?",
            "options": ["int", "str", "char", "float"],
            "correct_index": 2,
            "explanation": "Python does not have a 'char' type. Single characters are strings of length 1.",
            "position": 40,
        },
        {
            "question_text": "How do you open a file for reading in Python?",
            "options": [
                "open('file.txt', 'w')",
                "open('file.txt', 'r')",
                "read('file.txt')",
                "file.open('file.txt')",
            ],
            "correct_index": 1,
            "explanation": "open() with 'r' mode opens a file for reading.",
            "position": 50,
        },
    ],
    "JavaScript Essentials": [
        {
            "question_text": "Which keyword declares a variable that cannot be reassigned?",
            "options": ["var", "let", "const", "static"],
            "correct_index": 2,
            "explanation": "'const' declares a variable that cannot be reassigned.",
            "position": 10,
        },
        {
            "question_text": "What does DOM stand for?",
            "options": [
                "Data Object Model",
                "Document Object Model",
                "Dynamic Output Module",
                "Display Object Manager",
            ],
            "correct_index": 1,
            "explanation": "DOM stands for Document Object Model.",
            "position": 20,
        },
        {
            "question_text": "Which method adds an element to the end of an array?",
            "options": ["append()", "push()", "add()", "insert()"],
            "correct_index": 1,
            "explanation": "The push() method adds elements to the end of an array.",
            "position": 30,
        },
        {
            "question_text": "What is the output of: typeof 42?",
            "options": ["'int'", "'number'", "'integer'", "'numeric'"],
            "correct_index": 1,
            "explanation": "typeof returns 'number' for both integers and floats in JavaScript.",
            "position": 40,
        },
        {
            "question_text": "Which syntax creates an arrow function?",
            "options": ["function() => {}", "() => {}", "=> () {}", "func() {}"],
            "correct_index": 1,
            "explanation": "Arrow functions use the () => {} syntax.",
            "position": 50,
        },
    ],
    "SQL for Beginners": [
        {
            "question_text": "Which SQL clause filters rows in a query?",
            "options": ["ORDER BY", "GROUP BY", "WHERE", "HAVING"],
            "correct_index": 2,
            "explanation": "WHERE filters individual rows. HAVING filters groups.",
            "position": 10,
        },
        {
            "question_text": "What does SELECT * FROM users return?",
            "options": [
                "The first row",
                "All columns from users",
                "Only the id column",
                "The row count",
            ],
            "correct_index": 1,
            "explanation": "SELECT * retrieves all columns from the specified table.",
            "position": 20,
        },
        {
            "question_text": "Which JOIN returns only rows with matches in both tables?",
            "options": ["LEFT JOIN", "RIGHT JOIN", "FULL JOIN", "INNER JOIN"],
            "correct_index": 3,
            "explanation": "INNER JOIN returns only rows where there is a match in both tables.",
            "position": 30,
        },
        {
            "question_text": "Which aggregate function counts the number of rows?",
            "options": ["SUM()", "COUNT()", "TOTAL()", "NUM()"],
            "correct_index": 1,
            "explanation": "COUNT() returns the number of rows matching the query.",
            "position": 40,
        },
        {
            "question_text": "What does ORDER BY name DESC do?",
            "options": ["Sorts ascending", "Sorts descending", "Deletes by name", "Groups by name"],
            "correct_index": 1,
            "explanation": "DESC means descending order. ASC is the default (ascending).",
            "position": 50,
        },
    ],
}


def seed_quiz_questions():
    from apps.courses.models import Course
    from apps.assessments.models import QuizQuestion

    for course_title, questions in QUIZ_QUESTIONS.items():
        try:
            course = Course.objects.get(title=course_title)
            for q in questions:
                QuizQuestion.objects.get_or_create(
                    course=course, question_text=q["question_text"], defaults=q
                )
            print(f"  Quiz questions seeded: {course_title}")
        except Course.DoesNotExist:
            print(f"  Course not found for quiz: {course_title}")
