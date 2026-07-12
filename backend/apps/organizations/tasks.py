from celery import shared_task

from apps.organizations.models import BulkImportJob, DataExportJob, EnterpriseReportJob
from apps.organizations.services import EnterpriseOrganizationService


@shared_task(name="apps.organizations.process_data_export")
def process_data_export(export_id: str):
    export_job = DataExportJob.objects.select_related("organization", "created_by").get(id=export_id)
    EnterpriseOrganizationService.process_export(export_job)
    return str(export_job.id)


@shared_task(name="apps.organizations.process_bulk_import")
def process_bulk_import(import_id: str):
    import_job = BulkImportJob.objects.select_related("organization", "created_by").get(id=import_id)
    EnterpriseOrganizationService.process_import(import_job)
    return str(import_job.id)


@shared_task(name="apps.organizations.process_enterprise_report")
def process_enterprise_report(report_id: str):
    report = EnterpriseReportJob.objects.select_related("organization", "created_by").get(id=report_id)
    EnterpriseOrganizationService.process_report(report)
    return str(report.id)


@shared_task(name="apps.organizations.expire_data_exports")
def expire_data_exports():
    return EnterpriseOrganizationService.expire_exports()
