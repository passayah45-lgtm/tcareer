"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ApplicationQuestionsManager } from "@/components/recruiter/ApplicationQuestionsManager";
import { JobForm } from "@/components/recruiter/JobForm";
import { EmptyState, RecruiterShell, useRecruiterContext } from "@/components/recruiter/RecruiterShell";
import { getOrganizationJobs, updateOrganizationJob } from "@/lib/api/recruiter.api";
import type { RecruiterJob, RecruiterJobPayload } from "@/types/recruiter.types";

function EditJobContent() {
  const params = useParams<{ jobId: string }>();
  const router = useRouter();
  const { organization } = useRecruiterContext();
  const [job, setJob] = useState<RecruiterJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!organization) return;
    getOrganizationJobs(organization.id)
      .then((items) => setJob(items.find((item) => item.id === params.jobId) || null))
      .catch(() => setError("Unable to load job."))
      .finally(() => setLoading(false));
  }, [organization, params.jobId]);

  async function submit(payload: RecruiterJobPayload) {
    if (!organization || !job) return;
    setSubmitting(true);
    try {
      await updateOrganizationJob(organization.id, job.id, payload);
      router.push(`/recruiter/jobs/${job.id}?org=${organization.id}`);
    } catch {
      setError("Unable to update job.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <div className="h-64 bg-muted rounded-xl animate-pulse" />;
  if (!job) return <EmptyState title="Job not found" body={error || "This job does not belong to the selected organization."} />;

  return (
    <div className="space-y-4">
      {error && <div className="alert-error">{error}</div>}
      <JobForm initialJob={job} submitting={submitting} onSubmit={submit} />
      {organization && <ApplicationQuestionsManager organizationId={organization.id} jobId={job.id} />}
    </div>
  );
}

export default function EditRecruiterJobPage() {
  return (
    <RecruiterShell title="Edit job" description="Update job details, requirements, salary, and application links.">
      <EditJobContent />
    </RecruiterShell>
  );
}
