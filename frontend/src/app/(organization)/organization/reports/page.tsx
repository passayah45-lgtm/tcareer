"use client";

import { useCallback, useEffect, useState } from "react";
import { OrganizationShell, OrgEmptyState, useOrganizationContext } from "@/components/organization/OrganizationShell";
import { createEnterpriseReport, downloadExport, getEnterpriseReports, getEnterpriseWorkerJobs } from "@/lib/api/organizations.api";
import type { EnterpriseReportJob, EnterpriseWorkerJobs } from "@/types/organization.types";

const REPORT_TYPES = [
  "enrollment_report",
  "placement_report",
  "hiring_report",
  "recruiter_activity_report",
  "certificate_completion_report",
  "course_completion_report",
  "department_summary_report",
  "cohort_summary_report",
  "organization_summary_report",
  "engagement_summary_report",
  "export_summary_report",
];

export default function OrganizationReportsPage() {
  const { organization } = useOrganizationContext();
  const [reportType, setReportType] = useState("organization_summary_report");
  const [fileFormat, setFileFormat] = useState("xlsx");
  const [reports, setReports] = useState<EnterpriseReportJob[]>([]);
  const [workerJobs, setWorkerJobs] = useState<EnterpriseWorkerJobs | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!organization) return;
    const [reportItems, workerItems] = await Promise.all([getEnterpriseReports(organization.id), getEnterpriseWorkerJobs(organization.id)]);
    setReports(reportItems);
    setWorkerJobs(workerItems);
  }, [organization]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      load().catch(() => setError("Unable to load enterprise reports."));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function queueReport() {
    if (!organization) return;
    await createEnterpriseReport(organization.id, reportType, fileFormat);
    await load();
  }

  async function download(report: EnterpriseReportJob) {
    if (!organization || !report.export) return;
    const blob = await downloadExport(organization.id, report.export.id);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = report.export.file_name || `${report.report_type}.xlsx`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <OrganizationShell title="Enterprise reports" description="Queue asynchronous enterprise reports and monitor worker-backed operations.">
      {error && <p className="text-sm text-destructive mb-4">{error}</p>}
      <section className="rounded-xl border border-border bg-card p-5 flex flex-col gap-3 md:flex-row md:items-end mb-6">
        <label className="block text-sm flex-1">Report type<select className="input mt-1" value={reportType} onChange={(event) => setReportType(event.target.value)}>{REPORT_TYPES.map((item) => <option key={item} value={item}>{item.replaceAll("_", " ")}</option>)}</select></label>
        <label className="block text-sm md:w-36">Format<select className="input mt-1" value={fileFormat} onChange={(event) => setFileFormat(event.target.value)}><option value="xlsx">XLSX</option><option value="csv">CSV</option></select></label>
        <button onClick={queueReport} className="btn-base btn-primary">Queue report</button>
      </section>
      <div className="grid gap-4 md:grid-cols-3 mb-6">
        <div className="stat-card"><span className="stat-value">{workerJobs?.exports.length ?? 0}</span><span className="stat-label">Export jobs</span></div>
        <div className="stat-card"><span className="stat-value">{workerJobs?.imports.length ?? 0}</span><span className="stat-label">Import jobs</span></div>
        <div className="stat-card"><span className="stat-value">{workerJobs?.reports.length ?? 0}</span><span className="stat-label">Report jobs</span></div>
      </div>
      {workerJobs && (
        <section className="rounded-xl border border-border bg-card p-5 mb-6">
          <h2 className="font-semibold mb-3">Worker verification</h2>
          <div className="grid gap-3 md:grid-cols-3">
            {workerJobs.worker_statuses.map((item) => (
              <div key={item.id} className="rounded-lg border border-border p-3 text-sm">
                <p className="font-medium">{item.worker_key.split(":")[0].replaceAll("_", " ")}</p>
                <p className="text-muted-foreground">Heartbeat: {item.last_heartbeat_at ? new Date(item.last_heartbeat_at).toLocaleString() : "none"}</p>
                <p className="text-muted-foreground">Avg duration: {item.average_duration_seconds}s</p>
                <p className="text-muted-foreground">Failures: {item.failure_count} | Stuck: {item.stuck_job_count}</p>
              </div>
            ))}
          </div>
        </section>
      )}
      {reports.length === 0 ? <OrgEmptyState title="No reports yet" body="Queue an enterprise report to generate a downloadable file." /> : (
        <section className="rounded-xl border border-border bg-card p-5">
          <div className="divide-y divide-border">
            {reports.map((report) => (
              <div key={report.id} className="py-3 grid gap-2 md:grid-cols-[1fr_120px_120px_1fr_auto] md:items-center text-sm">
                <span>{report.report_type.replaceAll("_", " ")}</span>
                <span>{report.status}</span>
                <span>{report.progress_percentage}%</span>
                <span className="text-muted-foreground">{new Date(report.created_at).toLocaleString()}</span>
                <button disabled={!report.export || report.export.status !== "completed"} onClick={() => download(report)} className="btn-sm btn-secondary disabled:opacity-50">Download</button>
              </div>
            ))}
          </div>
        </section>
      )}
    </OrganizationShell>
  );
}
