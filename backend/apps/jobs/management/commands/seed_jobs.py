"""
Seed demo job listings for T-Career.

Usage:
    python manage.py seed_jobs
"""

from django.core.management.base import BaseCommand
from django.db import transaction


DEMO_JOBS = [
    {
        "title": "Junior Backend Developer",
        "company_name": "TechStart Inc.",
        "location": "Remote",
        "job_type": "full_time",
        "experience_level": "entry",
        "description": "We are looking for a junior backend developer to join our growing engineering team. You will build and maintain REST APIs, work with PostgreSQL databases, and collaborate with frontend developers to deliver features.\n\nYou will work in a small team with experienced engineers who will mentor you. We value learning and growth over years of experience.",
        "requirements": ["Python", "Django or FastAPI", "PostgreSQL", "Git", "REST APIs"],
        "salary_min": 55000,
        "salary_max": 70000,
        "apply_url": "https://example.com/apply/junior-backend",
        "track_slug": "backend-developer",
    },
    {
        "title": "Frontend React Developer",
        "company_name": "ProductLab",
        "location": "New York, USA",
        "job_type": "full_time",
        "experience_level": "entry",
        "description": "ProductLab builds SaaS tools for small businesses. We need a frontend developer who can build clean, responsive interfaces using React and TypeScript.\n\nYou will work closely with our design team and have ownership of entire features from day one.",
        "requirements": ["React", "TypeScript", "CSS", "HTML", "Git"],
        "salary_min": 60000,
        "salary_max": 80000,
        "apply_url": "https://example.com/apply/frontend-react",
        "track_slug": "frontend-developer",
    },
    {
        "title": "Data Analyst",
        "company_name": "Analytics Co.",
        "location": "Remote",
        "job_type": "full_time",
        "experience_level": "entry",
        "description": "Analytics Co. helps e-commerce businesses understand their data. We are hiring a data analyst who can turn raw data into insights that drive business decisions.\n\nYou will write SQL queries, build dashboards in Tableau, and present findings to non-technical stakeholders weekly.",
        "requirements": ["SQL", "Python", "Pandas", "Data Visualisation", "Excel"],
        "salary_min": 50000,
        "salary_max": 65000,
        "apply_url": "https://example.com/apply/data-analyst",
        "track_slug": "data-analyst",
    },
    {
        "title": "Junior DevOps Engineer",
        "company_name": "CloudSystems Ltd.",
        "location": "London, UK",
        "job_type": "full_time",
        "experience_level": "entry",
        "description": "CloudSystems manages infrastructure for fintech companies. We are looking for a junior DevOps engineer to help us build and maintain CI/CD pipelines, manage AWS infrastructure, and improve our deployment processes.",
        "requirements": ["Docker", "AWS", "Linux", "Git", "CI/CD"],
        "salary_min": 45000,
        "salary_max": 60000,
        "apply_url": "https://example.com/apply/devops-junior",
        "track_slug": "devops-engineer",
    },
    {
        "title": "Python Developer Intern",
        "company_name": "DataBridge",
        "location": "Remote",
        "job_type": "internship",
        "experience_level": "entry",
        "description": "DataBridge is a data integration startup. Our 3-month paid internship is designed for students who have completed Python and SQL courses and want real-world experience building data pipelines.",
        "requirements": ["Python", "SQL", "Pandas", "Git"],
        "salary_min": 2000,
        "salary_max": 3000,
        "apply_url": "https://example.com/apply/python-intern",
        "track_slug": "backend-developer",
    },
    {
        "title": "Machine Learning Engineer",
        "company_name": "AI Ventures",
        "location": "San Francisco, USA",
        "job_type": "full_time",
        "experience_level": "mid",
        "description": "AI Ventures builds ML-powered products for the healthcare industry. We are looking for an ML engineer to design, train, and deploy models in production. You will work with PyTorch, MLflow, and AWS SageMaker.",
        "requirements": ["Python", "PyTorch", "scikit-learn", "Docker", "AWS", "MLflow"],
        "salary_min": 120000,
        "salary_max": 150000,
        "apply_url": "https://example.com/apply/ml-engineer",
        "track_slug": "ml-engineer",
    },
    {
        "title": "UI/UX Designer",
        "company_name": "DesignStudio",
        "location": "Remote",
        "job_type": "contract",
        "experience_level": "entry",
        "description": "DesignStudio creates digital products for startups. We need a UI/UX designer who can take a brief, conduct basic user research, create wireframes and high-fidelity designs in Figma, and hand off to developers.",
        "requirements": ["Figma", "User Research", "Wireframing", "Prototyping", "Design Systems"],
        "salary_min": 40000,
        "salary_max": 55000,
        "apply_url": "https://example.com/apply/ui-ux-designer",
        "track_slug": "ui-ux-designer",
    },
    {
        "title": "Cloud Engineer",
        "company_name": "Nexus Cloud",
        "location": "Remote",
        "job_type": "full_time",
        "experience_level": "entry",
        "description": "Nexus Cloud provides managed cloud services. We are hiring a cloud engineer to help clients migrate to AWS, set up secure and scalable infrastructure, and maintain production environments.",
        "requirements": ["AWS", "Terraform", "Docker", "Linux", "Networking"],
        "salary_min": 70000,
        "salary_max": 90000,
        "apply_url": "https://example.com/apply/cloud-engineer",
        "track_slug": "cloud-engineer",
    },
]


class Command(BaseCommand):
    help = "Seed demo job listings."

    @transaction.atomic
    def handle(self, *args, **options):
        from apps.jobs.models import JobListing
        from apps.tracks.models import CareerTrack

        created = 0
        for job_data in DEMO_JOBS:
            track_slug = job_data.pop("track_slug", None)
            track = None
            if track_slug:
                try:
                    track = CareerTrack.objects.get(slug=track_slug)
                except CareerTrack.DoesNotExist:
                    pass

            _, was_created = JobListing.objects.get_or_create(
                title=job_data["title"],
                company_name=job_data["company_name"],
                defaults={**job_data, "required_track": track},
            )
            if was_created:
                created += 1
                self.stdout.write(f"  Created: {job_data['title']} at {job_data['company_name']}")

        self.stdout.write(self.style.SUCCESS(f"\n{created} job listings created."))
