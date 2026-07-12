from django.core.management.base import BaseCommand
from django.db import transaction

from apps.jobs.management.commands.recruiter_demo import ensure_demo_commands_allowed, reset_recruiter_demo_data


class Command(BaseCommand):
    help = "Remove only recruiter demo data created by seed_recruiter_demo."

    @transaction.atomic
    def handle(self, *args, **options):
        ensure_demo_commands_allowed()
        reset_recruiter_demo_data()
        self.stdout.write(self.style.SUCCESS("Recruiter demo data reset."))
