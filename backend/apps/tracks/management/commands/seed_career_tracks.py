"""
Seed all 13 career tracks with their course mappings.

Usage:
    python manage.py seed_career_tracks
    python manage.py seed_career_tracks --clear
"""

from django.core.management.base import BaseCommand
from django.db import transaction


TRACKS = [
    {
        "title": "Data Analyst",
        "slug": "data-analyst",
        "short_description": "Learn to collect, analyse, and visualise data to drive business decisions.",
        "description": "The Data Analyst track takes you from zero to job-ready in 4 to 6 months. You will master SQL, Python, and data visualisation tools used daily by analysts at top companies. By the end, you will be able to clean datasets, build dashboards, and present findings to stakeholders.",
        "category": "data_ai",
        "difficulty": "beginner",
        "icon": "bar-chart",
        "color": "#0ea5e9",
        "target_job_titles": ["Data Analyst", "Business Analyst", "Reporting Analyst", "BI Analyst"],
        "skills_acquired": ["SQL", "Python", "Pandas", "Data Visualisation", "Statistics", "Excel", "Tableau"],
        "estimated_weeks_min": 16,
        "estimated_weeks_max": 24,
        "avg_salary_min": 55000,
        "avg_salary_max": 75000,
        "position": 1,
        "courses": [
            {"slug": "sql-for-beginners", "stage": 1, "position": 10, "is_required": True},
            {"slug": "python-fundamentals-for-absolute-beginners", "stage": 1, "position": 20, "is_required": True},
            {"slug": "data-analysis-with-python-and-pandas", "stage": 2, "position": 30, "is_required": True},
            {"slug": "data-visualization-with-python", "stage": 2, "position": 40, "is_required": True},
            {"slug": "postgresql-for-developers", "stage": 3, "position": 50, "is_required": False},
        ],
    },
    {
        "title": "Data Scientist",
        "slug": "data-scientist",
        "short_description": "Build predictive models and extract insights from complex datasets.",
        "description": "The Data Scientist track covers the full spectrum from data wrangling to machine learning model deployment. You will work with real datasets, build classification and regression models, and learn to communicate findings to non-technical stakeholders.",
        "category": "data_ai",
        "difficulty": "intermediate",
        "icon": "flask",
        "color": "#8b5cf6",
        "target_job_titles": ["Data Scientist", "Research Analyst", "Quantitative Analyst", "ML Researcher"],
        "skills_acquired": ["Python", "Statistics", "Machine Learning", "Pandas", "scikit-learn", "Feature Engineering", "Model Evaluation"],
        "estimated_weeks_min": 24,
        "estimated_weeks_max": 32,
        "avg_salary_min": 80000,
        "avg_salary_max": 110000,
        "position": 2,
        "courses": [
            {"slug": "python-fundamentals-for-absolute-beginners", "stage": 1, "position": 10, "is_required": True},
            {"slug": "sql-for-beginners", "stage": 1, "position": 20, "is_required": True},
            {"slug": "data-analysis-with-python-and-pandas", "stage": 2, "position": 30, "is_required": True},
            {"slug": "machine-learning-fundamentals-with-python", "stage": 2, "position": 40, "is_required": True},
            {"slug": "data-visualization-with-python", "stage": 2, "position": 50, "is_required": True},
        ],
    },
    {
        "title": "AI Engineer",
        "slug": "ai-engineer",
        "short_description": "Build AI-powered applications using modern LLMs and APIs.",
        "description": "The AI Engineer track focuses on applied AI development. You will learn to integrate OpenAI and other LLM APIs, build intelligent applications, implement RAG systems, and deploy AI features in production. This is the fastest-growing role in tech.",
        "category": "data_ai",
        "difficulty": "intermediate",
        "icon": "cpu",
        "color": "#f59e0b",
        "target_job_titles": ["AI Engineer", "LLM Engineer", "Applied AI Developer", "AI Product Engineer"],
        "skills_acquired": ["Python", "OpenAI API", "LLM Integration", "Prompt Engineering", "Vector Databases", "RAG", "API Development"],
        "estimated_weeks_min": 24,
        "estimated_weeks_max": 32,
        "avg_salary_min": 100000,
        "avg_salary_max": 140000,
        "position": 3,
        "courses": [
            {"slug": "python-fundamentals-for-absolute-beginners", "stage": 1, "position": 10, "is_required": True},
            {"slug": "machine-learning-fundamentals-with-python", "stage": 2, "position": 20, "is_required": True},
            {"slug": "python-for-web-development-with-django", "stage": 2, "position": 30, "is_required": False},
        ],
    },
    {
        "title": "Machine Learning Engineer",
        "slug": "ml-engineer",
        "short_description": "Design, build, and deploy machine learning systems at scale.",
        "description": "The ML Engineer track bridges data science and software engineering. You will learn to build ML pipelines, serve models in production, monitor drift, and automate retraining. Strong Python and infrastructure skills are built throughout the track.",
        "category": "data_ai",
        "difficulty": "advanced",
        "icon": "git-branch",
        "color": "#ef4444",
        "target_job_titles": ["ML Engineer", "MLOps Engineer", "AI Platform Engineer", "ML Infrastructure Engineer"],
        "skills_acquired": ["Python", "PyTorch", "scikit-learn", "Docker", "Kubernetes", "MLflow", "Model Serving", "Pipeline Automation"],
        "estimated_weeks_min": 32,
        "estimated_weeks_max": 40,
        "avg_salary_min": 110000,
        "avg_salary_max": 150000,
        "position": 4,
        "courses": [
            {"slug": "python-fundamentals-for-absolute-beginners", "stage": 1, "position": 10, "is_required": True},
            {"slug": "git-and-github-for-developers", "stage": 1, "position": 20, "is_required": True},
            {"slug": "machine-learning-fundamentals-with-python", "stage": 2, "position": 30, "is_required": True},
            {"slug": "docker-and-containerization-from-scratch", "stage": 2, "position": 40, "is_required": True},
            {"slug": "aws-cloud-fundamentals", "stage": 3, "position": 50, "is_required": True},
        ],
    },
    {
        "title": "Full Stack Developer",
        "slug": "full-stack-developer",
        "short_description": "Build complete web applications from database to user interface.",
        "description": "The Full Stack Developer track covers both frontend and backend development. You will build real projects using React, Node.js, and PostgreSQL, then deploy them to the cloud. This track produces well-rounded engineers who can own features end to end.",
        "category": "tech",
        "difficulty": "beginner",
        "icon": "layers",
        "color": "#10b981",
        "target_job_titles": ["Full Stack Developer", "Software Engineer", "Web Developer", "Application Developer"],
        "skills_acquired": ["HTML", "CSS", "JavaScript", "TypeScript", "React", "Node.js", "PostgreSQL", "Docker", "REST APIs", "Git"],
        "estimated_weeks_min": 24,
        "estimated_weeks_max": 32,
        "avg_salary_min": 70000,
        "avg_salary_max": 95000,
        "position": 5,
        "courses": [
            {"slug": "html-and-css-from-zero", "stage": 1, "position": 10, "is_required": True},
            {"slug": "javascript-essentials", "stage": 1, "position": 20, "is_required": True},
            {"slug": "git-and-github-for-developers", "stage": 1, "position": 30, "is_required": True},
            {"slug": "react-from-zero-to-first-app", "stage": 2, "position": 40, "is_required": True},
            {"slug": "nodejs-and-express-backend-development", "stage": 2, "position": 50, "is_required": True},
            {"slug": "postgresql-for-developers", "stage": 2, "position": 60, "is_required": True},
            {"slug": "typescript-for-javascript-developers", "stage": 3, "position": 70, "is_required": True},
            {"slug": "docker-and-containerization-from-scratch", "stage": 3, "position": 80, "is_required": False},
        ],
    },
    {
        "title": "Frontend Developer",
        "slug": "frontend-developer",
        "short_description": "Build fast, accessible, and beautiful user interfaces for the web.",
        "description": "The Frontend Developer track teaches you to build modern web interfaces using React and TypeScript. You will cover responsive design, component architecture, performance optimisation, and accessibility. By the end, you will have a portfolio of real projects.",
        "category": "tech",
        "difficulty": "beginner",
        "icon": "monitor",
        "color": "#06b6d4",
        "target_job_titles": ["Frontend Developer", "React Developer", "UI Developer", "Web Developer"],
        "skills_acquired": ["HTML", "CSS", "JavaScript", "TypeScript", "React", "Next.js", "Figma", "Responsive Design", "Web Performance"],
        "estimated_weeks_min": 20,
        "estimated_weeks_max": 24,
        "avg_salary_min": 65000,
        "avg_salary_max": 90000,
        "position": 6,
        "courses": [
            {"slug": "html-and-css-from-zero", "stage": 1, "position": 10, "is_required": True},
            {"slug": "javascript-essentials", "stage": 1, "position": 20, "is_required": True},
            {"slug": "git-and-github-for-developers", "stage": 1, "position": 30, "is_required": True},
            {"slug": "react-from-zero-to-first-app", "stage": 2, "position": 40, "is_required": True},
            {"slug": "typescript-for-javascript-developers", "stage": 2, "position": 50, "is_required": True},
            {"slug": "ui-ux-design-fundamentals-with-figma", "stage": 3, "position": 60, "is_required": False},
        ],
    },
    {
        "title": "Backend Developer",
        "slug": "backend-developer",
        "short_description": "Build reliable, scalable server-side applications and APIs.",
        "description": "The Backend Developer track teaches you to build production-grade APIs with Python and Django. You will cover authentication, database design, caching, background tasks, and deployment. By the end, you will be able to architect and build backend systems from scratch.",
        "category": "tech",
        "difficulty": "beginner",
        "icon": "server",
        "color": "#6366f1",
        "target_job_titles": ["Backend Developer", "Python Developer", "API Engineer", "Software Engineer"],
        "skills_acquired": ["Python", "Django", "PostgreSQL", "REST APIs", "Docker", "AWS", "Authentication", "Redis", "Celery"],
        "estimated_weeks_min": 24,
        "estimated_weeks_max": 28,
        "avg_salary_min": 70000,
        "avg_salary_max": 95000,
        "position": 7,
        "courses": [
            {"slug": "python-fundamentals-for-absolute-beginners", "stage": 1, "position": 10, "is_required": True},
            {"slug": "sql-for-beginners", "stage": 1, "position": 20, "is_required": True},
            {"slug": "git-and-github-for-developers", "stage": 1, "position": 30, "is_required": True},
            {"slug": "python-for-web-development-with-django", "stage": 2, "position": 40, "is_required": True},
            {"slug": "postgresql-for-developers", "stage": 2, "position": 50, "is_required": True},
            {"slug": "docker-and-containerization-from-scratch", "stage": 3, "position": 60, "is_required": True},
            {"slug": "aws-cloud-fundamentals", "stage": 3, "position": 70, "is_required": False},
        ],
    },
    {
        "title": "Cloud Engineer",
        "slug": "cloud-engineer",
        "short_description": "Design, deploy, and manage cloud infrastructure on AWS.",
        "description": "The Cloud Engineer track covers AWS core services, infrastructure as code, and cloud architecture patterns. You will deploy real applications, configure networking and security, and learn the skills needed for AWS certification.",
        "category": "tech",
        "difficulty": "intermediate",
        "icon": "cloud",
        "color": "#f97316",
        "target_job_titles": ["Cloud Engineer", "AWS Engineer", "Solutions Architect", "Cloud Developer"],
        "skills_acquired": ["AWS", "Docker", "Kubernetes", "Terraform", "IAM", "Networking", "Monitoring", "Cost Optimisation"],
        "estimated_weeks_min": 24,
        "estimated_weeks_max": 32,
        "avg_salary_min": 85000,
        "avg_salary_max": 120000,
        "position": 8,
        "courses": [
            {"slug": "git-and-github-for-developers", "stage": 1, "position": 10, "is_required": True},
            {"slug": "docker-and-containerization-from-scratch", "stage": 2, "position": 20, "is_required": True},
            {"slug": "aws-cloud-fundamentals", "stage": 2, "position": 30, "is_required": True},
            {"slug": "cybersecurity-fundamentals", "stage": 3, "position": 40, "is_required": False},
        ],
    },
    {
        "title": "DevOps Engineer",
        "slug": "devops-engineer",
        "short_description": "Automate, scale, and secure software delivery pipelines.",
        "description": "The DevOps Engineer track covers CI/CD, containerisation, and infrastructure automation. You will build deployment pipelines, manage Kubernetes clusters, and implement monitoring and alerting systems used by engineering teams at scale.",
        "category": "tech",
        "difficulty": "intermediate",
        "icon": "repeat",
        "color": "#84cc16",
        "target_job_titles": ["DevOps Engineer", "Platform Engineer", "SRE", "Infrastructure Engineer"],
        "skills_acquired": ["Linux", "Git", "Docker", "Kubernetes", "CI/CD", "Terraform", "AWS", "Monitoring", "Incident Response"],
        "estimated_weeks_min": 24,
        "estimated_weeks_max": 32,
        "avg_salary_min": 90000,
        "avg_salary_max": 125000,
        "position": 9,
        "courses": [
            {"slug": "git-and-github-for-developers", "stage": 1, "position": 10, "is_required": True},
            {"slug": "python-fundamentals-for-absolute-beginners", "stage": 1, "position": 20, "is_required": False},
            {"slug": "docker-and-containerization-from-scratch", "stage": 2, "position": 30, "is_required": True},
            {"slug": "aws-cloud-fundamentals", "stage": 2, "position": 40, "is_required": True},
        ],
    },
    {
        "title": "Cybersecurity Analyst",
        "slug": "cybersecurity-analyst",
        "short_description": "Protect systems and data from threats and vulnerabilities.",
        "description": "The Cybersecurity Analyst track covers the fundamentals of network security, vulnerability assessment, and incident response. You will learn to think like an attacker to better defend systems and applications.",
        "category": "tech",
        "difficulty": "beginner",
        "icon": "shield",
        "color": "#dc2626",
        "target_job_titles": ["SOC Analyst", "Security Analyst", "Information Security Analyst", "Penetration Tester"],
        "skills_acquired": ["Network Security", "Linux", "Vulnerability Assessment", "SIEM", "Incident Response", "OWASP", "Cloud Security"],
        "estimated_weeks_min": 24,
        "estimated_weeks_max": 32,
        "avg_salary_min": 65000,
        "avg_salary_max": 90000,
        "position": 10,
        "courses": [
            {"slug": "cybersecurity-fundamentals", "stage": 1, "position": 10, "is_required": True},
            {"slug": "python-fundamentals-for-absolute-beginners", "stage": 1, "position": 20, "is_required": False},
            {"slug": "aws-cloud-fundamentals", "stage": 3, "position": 30, "is_required": False},
        ],
    },
    {
        "title": "Product Manager",
        "slug": "product-manager",
        "short_description": "Lead product teams from idea to launch with data and strategy.",
        "description": "The Product Manager track teaches the full product lifecycle from user research to launch metrics. You will learn to write PRDs, run sprint ceremonies, define success metrics, and work effectively with engineering and design teams.",
        "category": "design",
        "difficulty": "beginner",
        "icon": "target",
        "color": "#7c3aed",
        "target_job_titles": ["Associate PM", "Junior Product Manager", "Technical PM", "Product Analyst"],
        "skills_acquired": ["Product Strategy", "User Research", "Roadmapping", "Agile", "Data Analysis", "Stakeholder Management", "PRD Writing"],
        "estimated_weeks_min": 16,
        "estimated_weeks_max": 24,
        "avg_salary_min": 75000,
        "avg_salary_max": 100000,
        "position": 11,
        "courses": [
            {"slug": "product-management-for-tech-professionals", "stage": 1, "position": 10, "is_required": True},
            {"slug": "sql-for-beginners", "stage": 2, "position": 20, "is_required": True},
            {"slug": "ui-ux-design-fundamentals-with-figma", "stage": 2, "position": 30, "is_required": False},
        ],
    },
    {
        "title": "UI/UX Designer",
        "slug": "ui-ux-designer",
        "short_description": "Design user interfaces that are both beautiful and easy to use.",
        "description": "The UI/UX Designer track covers the full design process from research to high-fidelity prototypes. You will master Figma, learn to conduct user research, and build a portfolio of real projects that demonstrate your ability to solve user problems.",
        "category": "design",
        "difficulty": "beginner",
        "icon": "pen-tool",
        "color": "#ec4899",
        "target_job_titles": ["UI Designer", "UX Designer", "Product Designer", "Interaction Designer"],
        "skills_acquired": ["Figma", "Wireframing", "Prototyping", "User Research", "Design Systems", "Usability Testing", "HTML/CSS Basics"],
        "estimated_weeks_min": 16,
        "estimated_weeks_max": 24,
        "avg_salary_min": 60000,
        "avg_salary_max": 85000,
        "position": 12,
        "courses": [
            {"slug": "ui-ux-design-fundamentals-with-figma", "stage": 1, "position": 10, "is_required": True},
            {"slug": "html-and-css-from-zero", "stage": 2, "position": 20, "is_required": False},
        ],
    },
    {
        "title": "Digital Marketer",
        "slug": "digital-marketer",
        "short_description": "Grow businesses through data-driven digital marketing strategies.",
        "description": "The Digital Marketer track covers SEO, paid advertising, email marketing, and analytics. You will learn to build and execute campaigns across multiple channels, measure results, and continuously improve performance using data.",
        "category": "business",
        "difficulty": "beginner",
        "icon": "trending-up",
        "color": "#059669",
        "target_job_titles": ["Digital Marketing Specialist", "SEO Analyst", "Growth Marketer", "Marketing Analyst"],
        "skills_acquired": ["SEO", "Google Ads", "Email Marketing", "Content Strategy", "Analytics", "A/B Testing", "Social Media"],
        "estimated_weeks_min": 16,
        "estimated_weeks_max": 24,
        "avg_salary_min": 50000,
        "avg_salary_max": 70000,
        "position": 13,
        "courses": [
            {"slug": "english-for-tech-professionals", "stage": 1, "position": 10, "is_required": False},
        ],
    },
]


class Command(BaseCommand):
    help = "Seed all 13 career tracks with course mappings."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing tracks before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        from apps.tracks.models import CareerTrack, TrackCourse
        from apps.courses.models import Course

        if options["clear"]:
            CareerTrack.objects.all().delete()
            self.stdout.write("Cleared existing tracks.")

        created_count = 0
        skipped_count = 0

        for track_data in TRACKS:
            courses_data = track_data.pop("courses", [])

            track, created = CareerTrack.objects.update_or_create(
                slug=track_data["slug"],
                defaults=track_data,
            )

            if created:
                created_count += 1
            else:
                skipped_count += 1

            for course_entry in courses_data:
                course_slug = course_entry.pop("slug")
                try:
                    course = Course.objects.get(slug=course_slug)
                    TrackCourse.objects.update_or_create(
                        track=track,
                        course=course,
                        defaults=course_entry,
                    )
                except Course.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Course not found: {course_slug} (skipped for track {track.title})"
                        )
                    )

            self.stdout.write(
                f"  {'Created' if created else 'Updated'}: {track.title}"
            )

        self.stdout.write(self.style.SUCCESS(
            f"\nCareer tracks seeded: {created_count} created, {skipped_count} updated."
        ))
