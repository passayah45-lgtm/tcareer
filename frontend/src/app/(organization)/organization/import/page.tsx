"use client";

import { MouseEvent, useState } from "react";
import { OrganizationShell, useOrganizationContext } from "@/components/organization/OrganizationShell";
import { bulkImport, downloadImportFile, downloadImportTemplate, getImportJobs, getImportTemplate } from "@/lib/api/organizations.api";
import type { BulkImportJob, ImportTemplate } from "@/types/organization.types";

const IMPORT_TYPES = ["students", "recruiters", "instructors", "employees", "departments", "teams", "cohorts", "skills", "courses", "course_assignments", "cohort_assignments"];

export default function OrganizationImportPage() {
  const { organization } = useOrganizationContext();
  const [importType, setImportType] = useState("students");
  const [csvContent, setCsvContent] = useState("email,full_name\nstudent@example.com,Student Example\n");
  const [job, setJob] = useState<BulkImportJob | null>(null);
  const [jobs, setJobs] = useState<BulkImportJob[]>([]);
  const [template, setTemplate] = useState<ImportTemplate | null>(null);
  const [error, setError] = useState("");

  async function runImport(event: MouseEvent<HTMLButtonElement>, commit: boolean) {
    event.preventDefault();
    if (!organization) return;
    setError("");
    try {
      const result = await bulkImport(organization.id, { import_type: importType, csv_content: csvContent, source_filename: "browser-import.csv", commit });
      setJob(result);
      setJobs(await getImportJobs(organization.id));
    } catch {
      setError("Unable to process import.");
    }
  }

  async function loadTemplate() {
    if (!organization) return;
    setTemplate(await getImportTemplate(organization.id, importType));
  }

  async function downloadTemplate() {
    if (!organization) return;
    const blob = await downloadImportTemplate(organization.id, importType);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${organization.slug}-${importType}-template.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }

  async function downloadJobFile(item: BulkImportJob, fileKind: "summary" | "errors") {
    if (!organization) return;
    const blob = await downloadImportFile(organization.id, item.id, fileKind);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${organization.slug}-${item.import_type}-${fileKind}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <OrganizationShell title="Bulk import" description="Preview and import members, departments, and teams from CSV.">
      <form className="rounded-xl border border-border bg-card p-5 space-y-4">
        {error && <p className="text-sm text-destructive">{error}</p>}
        <label className="block text-sm">Import type<select className="input mt-1" value={importType} onChange={(event) => setImportType(event.target.value)}>{IMPORT_TYPES.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={loadTemplate} className="btn-sm btn-secondary">Show template</button>
          <button type="button" onClick={downloadTemplate} className="btn-sm btn-secondary">Download template</button>
        </div>
        {template && (
          <div className="rounded-lg bg-muted p-3 text-xs">
            <p className="font-medium mb-1">Required columns: {template.required_columns.join(", ") || "none"}</p>
            <p className="text-muted-foreground">All columns: {template.columns.join(", ")}</p>
          </div>
        )}
        <label className="block text-sm">CSV<textarea className="input mt-1 min-h-64 font-mono text-xs" value={csvContent} onChange={(event) => setCsvContent(event.target.value)} /></label>
        <div className="flex gap-2">
          <button onClick={(event) => runImport(event, false)} className="btn-base btn-secondary">Preview</button>
          <button onClick={(event) => runImport(event, true)} className="btn-base btn-primary">Commit import</button>
        </div>
      </form>
      {job && (
        <section className="rounded-xl border border-border bg-card p-5 mt-6">
          <h2 className="font-semibold mb-3">Import result</h2>
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="stat-card"><span className="stat-value">{job.status}</span><span className="stat-label">Status</span></div>
            <div className="stat-card"><span className="stat-value">{job.progress_percentage}%</span><span className="stat-label">Progress</span></div>
            <div className="stat-card"><span className="stat-value">{job.success_count}</span><span className="stat-label">Success</span></div>
            <div className="stat-card"><span className="stat-value">{job.error_count}</span><span className="stat-label">Errors</span></div>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button disabled={!job.summary_file_url} onClick={() => downloadJobFile(job, "summary")} className="btn-sm btn-secondary disabled:opacity-50">Download summary</button>
            <button disabled={!job.error_file_url} onClick={() => downloadJobFile(job, "errors")} className="btn-sm btn-secondary disabled:opacity-50">Download errors</button>
          </div>
          {job.validation_errors.length > 0 && (
            <div className="mt-4 text-sm text-destructive">
              {job.validation_errors.map((item) => <p key={`${item.row}-${item.field}`}>Row {item.row}: {item.message}</p>)}
            </div>
          )}
          {job.partial_success_report.length > 0 && (
            <p className="mt-4 text-sm text-muted-foreground">Partial success: {JSON.stringify(job.partial_success_report[0])}</p>
          )}
        </section>
      )}
      {jobs.length > 0 && (
        <section className="rounded-xl border border-border bg-card p-5 mt-6">
          <h2 className="font-semibold mb-3">Recent import jobs</h2>
          <div className="divide-y divide-border">
            {jobs.map((item) => (
              <div key={item.id} className="py-3 grid gap-2 md:grid-cols-[1fr_100px_90px_90px_auto] md:items-center text-sm">
                <span>{item.import_type.replaceAll("_", " ")}</span>
                <span>{item.status}</span>
                <span>{item.success_count} ok</span>
                <span>{item.error_count} errors</span>
                <div className="flex gap-2">
                  <button disabled={!item.summary_file_url} onClick={() => downloadJobFile(item, "summary")} className="btn-sm btn-secondary disabled:opacity-50">Summary</button>
                  <button disabled={!item.error_file_url} onClick={() => downloadJobFile(item, "errors")} className="btn-sm btn-secondary disabled:opacity-50">Errors</button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </OrganizationShell>
  );
}
