from django.core.management.base import BaseCommand

from apps.organizations.models import DataExportJob, EnterpriseReportJob
from apps.organizations.services import EnterpriseOrganizationService


class Command(BaseCommand):
    help = "Process queued organization data exports."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)
        parser.add_argument("--expire", action="store_true")
        parser.add_argument("--delete-expired-files", action="store_true")
        parser.add_argument("--reports", action="store_true")

    def handle(self, *args, **options):
        limit = max(options["limit"], 1)
        jobs = DataExportJob.objects.filter(status=DataExportJob.Status.QUEUED).select_related("organization", "created_by").order_by("created_at")[:limit]
        processed = 0
        for job in jobs:
            EnterpriseOrganizationService.process_export(job)
            processed += 1
        if options["reports"]:
            reports = EnterpriseReportJob.objects.filter(status=EnterpriseReportJob.Status.QUEUED).select_related("organization", "created_by").order_by("created_at")[:limit]
            for report in reports:
                EnterpriseOrganizationService.process_report(report)
                processed += 1
        expired = EnterpriseOrganizationService.expire_exports(delete_files=options["delete_expired_files"]) if options["expire"] else 0
        self.stdout.write(self.style.SUCCESS(f"Processed {processed} data export job(s)."))
        if options["expire"]:
            self.stdout.write(self.style.SUCCESS(f"Expired {expired} completed export job(s)."))
