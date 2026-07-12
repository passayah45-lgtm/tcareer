"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { EmptyState, RecruiterShell, useRecruiterContext } from "@/components/recruiter/RecruiterShell";
import { archiveOrganizationJob, getOrganizationJobs, publishOrganizationJob } from "@/lib/api/recruiter.api";
import type { RecruiterJob } from "@/types/recruiter.types";

function JobsContent() {
  const { organization } = useRecruiterContext();
  const [jobs, setJobs] = useState<RecruiterJob[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!organization) return;
    setLoading(true);
    try {
      setJobs(await getOrganizationJobs(organization.id));
      setError("");
    } catch {
      setError("Unable to load organization jobs.");
    } finally {
      setLoading(false);
    }
  }, [organization]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return jobs.filter((job) => !q || job.title.toLowerCase().includes(q) || job.company_name.toLowerCase().includes(q));
  }, [jobs, search]);

  async function toggle(job: RecruiterJob) {
    if (!organization) return;
    if (job.is_active) await archiveOrganizationJob(organization.id, job.id);
    else await publishOrganizationJob(organization.id, job.id);
    await load();
  }

  if (!organization) return null;

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
        <input className="input max-w-sm" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search jobs..." />
        <Link href={`/recruiter/jobs/new?org=${organization.id}`} className="btn-base btn-primary">Create job</Link>
      </div>

      {loading ? <div className="h-52 bg-muted rounded-xl animate-pulse" /> : null}
      {error ? <EmptyState title="Jobs unavailable" body={error} /> : null}
      {!loading && !error && filtered.length === 0 ? (
        <EmptyState title="No jobs yet" body="Create a draft job to start hiring from your organization." />
      ) : null}

      <div className="space-y-3">
        {filtered.map((job) => (
          <div key={job.id} className="border border-border rounded-xl bg-card p-5 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="font-semibold">{job.title}</h2>
                <span className={`badge ${job.is_active ? "badge-success" : "badge-warning"}`}>{job.is_active ? "Published" : "Draft/Archived"}</span>
              </div>
              <p className="text-sm text-muted-foreground mt-1">{job.company_name} - {job.location || "Location not set"}</p>
              <p className="text-xs text-muted-foreground mt-1">{job.experience_level_display} - {job.salary_display}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link href={`/recruiter/jobs/${job.id}?org=${organization.id}`} className="btn-sm btn-secondary">Detail</Link>
              <Link href={`/recruiter/jobs/${job.id}/edit?org=${organization.id}`} className="btn-sm btn-secondary">Edit</Link>
              <button onClick={() => toggle(job)} className={job.is_active ? "btn-sm btn-secondary" : "btn-sm btn-primary"}>
                {job.is_active ? "Archive" : "Publish"}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function RecruiterJobsPage() {
  return (
    <RecruiterShell title="Organization jobs" description="Create, publish, archive, and review applications for your organization jobs.">
      <JobsContent />
    </RecruiterShell>
  );
}
