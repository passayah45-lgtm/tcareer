"use client";

import { useCallback, useEffect, useState } from "react";
import { OrganizationShell, OrgEmptyState, useOrganizationContext } from "@/components/organization/OrganizationShell";
import { createExport, downloadExport, getExports } from "@/lib/api/organizations.api";
import type { DataExportJob } from "@/types/organization.types";

const EXPORT_TYPES = [
  "students",
  "recruiters",
  "applications",
  "certificates",
  "courses",
  "audit_logs",
  "analytics_summary",
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

export default function OrganizationExportPage() {
  const { organization } = useOrganizationContext();
  const [exportType, setExportType] = useState("students");
  const [fileFormat, setFileFormat] = useState("csv");
  const [exports, setExports] = useState<DataExportJob[]>([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!organization) return;
    setExports(await getExports(organization.id));
  }, [organization]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      load().catch(() => setError("Unable to load exports."));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function generate() {
    if (!organization) return;
    setError("");
    try {
      await createExport(organization.id, exportType, fileFormat);
      await load();
    } catch {
      setError("Unable to generate export.");
    }
  }

  async function download(item: DataExportJob) {
    if (!organization) return;
    const blob = await downloadExport(organization.id, item.id);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = item.file_name || `${organization.slug}-${item.export_type}.${item.file_format}`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <OrganizationShell title="Data export" description="Generate organization-scoped operational exports for admins.">
      {error && <p className="text-sm text-destructive mb-4">{error}</p>}
      <section className="rounded-xl border border-border bg-card p-5 flex flex-col gap-3 md:flex-row md:items-end mb-6">
        <label className="block text-sm flex-1">Export type<select className="input mt-1" value={exportType} onChange={(event) => setExportType(event.target.value)}>{EXPORT_TYPES.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
        <label className="block text-sm w-full md:w-40">Format<select className="input mt-1" value={fileFormat} onChange={(event) => setFileFormat(event.target.value)}><option value="csv">CSV</option><option value="xlsx">XLSX</option></select></label>
        <button onClick={generate} className="btn-base btn-primary">Queue export</button>
      </section>
      {exports.length === 0 ? <OrgEmptyState title="No exports yet" body="Generated export jobs will appear here." /> : (
        <section className="rounded-xl border border-border bg-card p-5">
          <h2 className="font-semibold mb-4">Recent exports</h2>
          <div className="divide-y divide-border">
            {exports.map((item) => (
              <div key={item.id} className="py-3 text-sm grid gap-1 md:grid-cols-[1fr_80px_100px_100px_120px_1fr_auto] md:items-center">
                <span>{item.export_type.replaceAll("_", " ")}</span>
                <span>{item.file_format}</span>
                <span>{item.status}</span>
                <span>{item.row_count} rows</span>
                <span>{item.download_count} downloads</span>
                <span className="text-muted-foreground">{new Date(item.created_at).toLocaleString()}</span>
                <button disabled={item.status !== "completed"} onClick={() => download(item)} className="btn-sm btn-secondary disabled:opacity-50">Download</button>
              </div>
            ))}
          </div>
        </section>
      )}
    </OrganizationShell>
  );
}
