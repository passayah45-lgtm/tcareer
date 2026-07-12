"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ApplicationQuestionsManager } from "@/components/recruiter/ApplicationQuestionsManager";
import { EmptyState, RecruiterShell, useRecruiterContext } from "@/components/recruiter/RecruiterShell";
import { archiveOrganizationJob, getOrganizationJobs, getPipelineApplications, publishOrganizationJob } from "@/lib/api/recruiter.api";
import type { JobApplication, RecruiterJob } from "@/types/recruiter.types";

function JobDetailContent() {
  const params = useParams<{ jobId: string }>();
  const { organization } = useRecruiterContext();
  const [job, setJob] = useState<RecruiterJob | null>(null);
  const [applications, setApplications] = useState<JobApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!organization) return;
    setLoading(true);
    try {
      const [jobs, pipeline] = await Promise.all([
        getOrganizationJobs(organization.id),
        getPipelineApplications(organization.id, { job_id: params.jobId, page_size: 100 }),
      ]);
      setJob(jobs.find((item) => item.id === params.jobId) || null);
      setApplications(pipeline.data);
      setError("");
    } catch {
      setError("Unable to load job detail.");
    } finally {
      setLoading(false);
    }
  }, [organization, params.jobId]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const stageCounts = useMemo(() => applications.reduce<Record<string, number>>((acc, item) => {
    acc[item.stage] = (acc[item.stage] || 0) + 1;
    return acc;
  }, {}), [applications]);

  async function toggle() {
    if (!organization || !job) return;
    if (job.is_active) await archiveOrganizationJob(organization.id, job.id);
    else await publishOrganizationJob(organization.id, job.id);
    await load();
  }

  if (loading) return <div className="h-64 bg-muted rounded-xl animate-pulse" />;
  if (!job) return <EmptyState title="Job not found" body={error || "This job is unavailable for the selected organization."} />;
  if (!organization) return null;

  return (
    <div className="space-y-6">
      <section className="border border-border rounded-xl bg-card p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-xl font-bold">{job.title}</h2>
              <span className={`badge ${job.is_active ? "badge-success" : "badge-warning"}`}>{job.is_active ? "Published" : "Draft/Archived"}</span>
            </div>
            <p className="text-sm text-muted-foreground mt-1">{job.company_name} - {job.location || "Location not set"}</p>
            <p className="text-sm mt-4 whitespace-pre-wrap">{job.description}</p>
          </div>
          <div className="flex gap-2 shrink-0">
            <Link href={`/recruiter/jobs/${job.id}/edit?org=${organization.id}`} className="btn-sm btn-secondary">Edit</Link>
            <button onClick={toggle} className={job.is_active ? "btn-sm btn-secondary" : "btn-sm btn-primary"}>{job.is_active ? "Archive" : "Publish"}</button>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6">
          <div className="stat-card"><span className="stat-value">{applications.length}</span><span className="stat-label">Applications</span></div>
          <div className="stat-card"><span className="stat-value">{stageCounts.shortlisted || 0}</span><span className="stat-label">Shortlisted</span></div>
          <div className="stat-card"><span className="stat-value">{stageCounts.interview_scheduled || 0}</span><span className="stat-label">Interviews</span></div>
          <div className="stat-card"><span className="stat-value">{job.views_count}</span><span className="stat-label">Views</span></div>
        </div>
      </section>

      <ApplicationQuestionsManager organizationId={organization.id} jobId={job.id} />

      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold">Applications for this job</h2>
          <Link href={`/recruiter/pipeline?org=${organization.id}&job_id=${job.id}`} className="text-sm text-primary hover:underline">Open in pipeline</Link>
        </div>
        {applications.length === 0 ? (
          <EmptyState title="No applications yet" body="Published jobs will show candidates here as they apply." />
        ) : (
          <div className="space-y-3">
            {applications.map((application) => (
              <Link key={application.id} href={`/recruiter/applications/${application.id}?org=${organization.id}`} className="block border border-border rounded-xl bg-card p-4 hover:shadow-sm transition-all">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-medium text-sm">{application.candidate_name}</p>
                    <p className="text-xs text-muted-foreground">{application.candidate_email}</p>
                  </div>
                  <span className="badge-primary capitalize">{application.stage_display}</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default function RecruiterJobDetailPage() {
  return (
    <RecruiterShell title="Job detail" description="Review job performance and applications.">
      <JobDetailContent />
    </RecruiterShell>
  );
}
