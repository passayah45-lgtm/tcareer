"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { EmptyState, RecruiterShell, useRecruiterContext } from "@/components/recruiter/RecruiterShell";
import { bulkArchiveApplications, bulkRejectApplications, changeApplicationStage, getPipelineApplications } from "@/lib/api/recruiter.api";
import type { ApplicationStage, JobApplication } from "@/types/recruiter.types";

const STAGES: Array<{ id: ApplicationStage; label: string }> = [
  { id: "applied", label: "Applied" },
  { id: "under_review", label: "Under Review" },
  { id: "shortlisted", label: "Shortlisted" },
  { id: "assessment", label: "Assessment" },
  { id: "interview_scheduled", label: "Interview Scheduled" },
  { id: "interview_completed", label: "Interview Completed" },
  { id: "offer_sent", label: "Offer Sent" },
  { id: "offer_accepted", label: "Offer Accepted" },
  { id: "offer_declined", label: "Offer Declined" },
  { id: "rejected", label: "Rejected" },
  { id: "withdrawn", label: "Withdrawn" },
];

function PipelineContent() {
  const { organization } = useRecruiterContext();
  const [applications, setApplications] = useState<JobApplication[]>([]);
  const [query, setQuery] = useState("");
  const [stage, setStage] = useState("");
  const [sort, setSort] = useState("-created_at");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [movingId, setMovingId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");

  const load = useCallback(async () => {
    if (!organization) return;
    setLoading(true);
    try {
      const jobId = typeof window !== "undefined" ? new URLSearchParams(window.location.search).get("job_id") : null;
      const result = await getPipelineApplications(organization.id, {
        search: query,
        stage,
        sort,
        job_id: jobId,
        page_size: 100,
      });
      setApplications(result.data);
      setError("");
      setActionError("");
    } catch {
      setError("Unable to load application pipeline.");
    } finally {
      setLoading(false);
    }
  }, [organization, query, sort, stage]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const grouped = useMemo(() => {
    const map = new Map<ApplicationStage, JobApplication[]>();
    STAGES.forEach((item) => map.set(item.id, []));
    applications.forEach((application) => map.get(application.stage)?.push(application));
    return map;
  }, [applications]);

  function toggleSelected(applicationId: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(applicationId)) next.delete(applicationId);
      else next.add(applicationId);
      return next;
    });
  }

  async function move(application: JobApplication, nextStage: ApplicationStage) {
    if (!organization) return;
    const previous = applications;
    setMovingId(application.id);
    setActionError("");
    setApplications((items) => items.map((item) => (item.id === application.id ? { ...item, stage: nextStage } : item)));
    try {
      await changeApplicationStage(organization.id, application.id, nextStage);
      await load();
    } catch {
      setApplications(previous);
      setActionError("Could not move application. The pipeline was restored.");
    } finally {
      setMovingId("");
    }
  }

  async function bulkReject() {
    if (!organization || selected.size === 0) return;
    try {
      await bulkRejectApplications(organization.id, Array.from(selected), "Bulk rejected from pipeline.");
      setSelected(new Set());
      await load();
    } catch {
      setActionError("Could not reject selected applications.");
    }
  }

  async function bulkArchive() {
    if (!organization || selected.size === 0) return;
    try {
      await bulkArchiveApplications(organization.id, Array.from(selected));
      setSelected(new Set());
      await load();
    } catch {
      setActionError("Could not archive selected applications.");
    }
  }

  if (!organization) return null;

  return (
    <div className="space-y-5">
      <div className="border border-border rounded-xl bg-card p-4 flex flex-col gap-3 lg:flex-row lg:items-center">
        <input className="input lg:max-w-xs" value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => event.key === "Enter" && load()} placeholder="Search candidate, email, or job..." />
        <select className="input lg:max-w-52" value={stage} onChange={(event) => setStage(event.target.value)}>
          <option value="">All stages</option>
          {STAGES.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
        </select>
        <select className="input lg:max-w-52" value={sort} onChange={(event) => setSort(event.target.value)}>
          <option value="-created_at">Newest</option>
          <option value="created_at">Oldest</option>
          <option value="stage">Stage</option>
        </select>
        <button onClick={load} className="btn-base btn-secondary">Filter</button>
        <div className="lg:ml-auto flex gap-2">
          <button onClick={bulkReject} disabled={selected.size === 0} className="btn-sm btn-secondary">Reject selected</button>
          <button onClick={bulkArchive} disabled={selected.size === 0} className="btn-sm btn-secondary">Archive selected</button>
        </div>
      </div>

      {loading ? <div className="h-72 bg-muted rounded-xl animate-pulse" /> : null}
      {error ? <EmptyState title="Pipeline unavailable" body={error} /> : null}
      {actionError ? <div className="border border-destructive/30 bg-destructive/10 text-destructive rounded-xl p-4 text-sm">{actionError}</div> : null}
      {!loading && !error && applications.length === 0 ? <EmptyState title="No applications" body="Applications will appear here when candidates apply to organization jobs." /> : null}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {STAGES.map((column) => {
          const items = grouped.get(column.id) || [];
          if (stage && stage !== column.id) return null;
          return (
            <section key={column.id} className="border border-border rounded-xl bg-muted/30 min-h-52">
              <div className="p-3 border-b border-border flex items-center justify-between">
                <h2 className="text-sm font-semibold">{column.label}</h2>
                <span className="badge-default">{items.length}</span>
              </div>
              <div className="p-3 space-y-3">
                {items.map((application) => (
                  <div key={application.id} className="bg-card border border-border rounded-xl p-4">
                    <div className="flex items-start gap-2">
                      <input type="checkbox" className="mt-1" checked={selected.has(application.id)} onChange={() => toggleSelected(application.id)} />
                      <div className="min-w-0 flex-1">
                        <p className="font-medium text-sm truncate">{application.candidate_name}</p>
                        <p className="text-xs text-muted-foreground truncate">{application.job_title}</p>
                        <p className="text-xs text-muted-foreground mt-1">{new Date(application.created_at).toLocaleDateString()}</p>
                      </div>
                    </div>
                    <div className="mt-3 flex gap-2">
                      <Link href={`/recruiter/applications/${application.id}?org=${organization.id}`} className="btn-sm btn-secondary">Open</Link>
                      <select
                        className="input-sm border rounded"
                        value={application.stage}
                        disabled={movingId === application.id}
                        onChange={(event) => move(application, event.target.value as ApplicationStage)}
                      >
                        {STAGES.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
                      </select>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}

export default function RecruiterPipelinePage() {
  return (
    <RecruiterShell title="Application pipeline" description="Search, filter, move, reject, archive, and open applications by hiring stage.">
      <PipelineContent />
    </RecruiterShell>
  );
}
