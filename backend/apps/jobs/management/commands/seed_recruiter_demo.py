from django.core.management.base import BaseCommand

from apps.jobs.management.commands.recruiter_demo import RecruiterDemoSeeder


class Command(BaseCommand):
    help = "Seed a dashboard-ready recruiter demo scenario."

    def handle(self, *args, **options):
        result = RecruiterDemoSeeder(stdout=self.stdout).seed()
        self.stdout.write(
            self.style.SUCCESS(
                "Recruiter demo data ready: "
                f"{result['users']} users, "
                f"{result['organizations']} organizations, "
                f"{result['jobs']} jobs, "
                f"{result['applications']} applications."
            )
        )
