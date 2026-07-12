import logging

from django.core.management.base import BaseCommand

from apps.jobs.services import JobAlertService

logger = logging.getLogger("tcareer.worker.job_alerts")


class Command(BaseCommand):
    help = "Run active student job alerts and create notifications for new matches."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit-per-alert",
            type=int,
            default=10,
            help="Maximum notifications to create per alert run.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximum total matches to create across this command run.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Evaluate matches without creating notifications, email delivery records, analytics, or run counters.",
        )

    def handle(self, *args, **options):
        summary = JobAlertService.run_active_alerts(
            limit_per_alert=options["limit_per_alert"],
            dry_run=options["dry_run"],
            limit=options["limit"],
        )
        logger.info("job_alert_command_completed", extra=summary)
        self.stdout.write(
            self.style.SUCCESS(
                "Checked {alerts_checked} alerts; {mode} {matches_created} matches "
                "and {email_payloads_created} email-ready payloads.".format(
                    mode="would create" if summary["dry_run"] else "created",
                    **summary,
                )
            )
        )
