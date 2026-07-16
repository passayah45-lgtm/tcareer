import logging

from django.core.management.base import BaseCommand

from apps.notifications.models import EmailDeliveryService

logger = logging.getLogger("tcareer.worker.email")


class Command(BaseCommand):
    help = "Process pending or failed email delivery records."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50, help="Maximum deliveries to process.")
        parser.add_argument(
            "--retry-failed",
            action="store_true",
            help="Retry failed deliveries instead of pending ones.",
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="List eligible deliveries without sending email."
        )

    def handle(self, *args, **options):
        limit = max(0, options["limit"])
        dry_run = options["dry_run"]
        if options["retry_failed"]:
            deliveries = EmailDeliveryService.retry_failed(limit=limit, dry_run=dry_run)
            label = "failed"
        else:
            deliveries = EmailDeliveryService.bulk_process_pending(limit=limit, dry_run=dry_run)
            label = "pending"

        mode = "Dry run" if dry_run else "Processed"
        logger.info(
            "email_delivery_command_completed",
            extra={
                "mode": mode.lower().replace(" ", "_"),
                "label": label,
                "count": len(deliveries),
                "limit": limit,
            },
        )
        self.stdout.write(self.style.SUCCESS(f"{mode} {len(deliveries)} {label} email deliveries."))
