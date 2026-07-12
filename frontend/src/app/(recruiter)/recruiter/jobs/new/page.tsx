"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { JobForm } from "@/components/recruiter/JobForm";
import { RecruiterShell, useRecruiterContext } from "@/components/recruiter/RecruiterShell";
import { createOrganizationJob } from "@/lib/api/recruiter.api";
import type { RecruiterJobPayload } from "@/types/recruiter.types";

function NewJobContent() {
  const router = useRouter();
  const { organization } = useRecruiterContext();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function submit(payload: RecruiterJobPayload) {
    if (!organization) return;
    setSubmitting(true);
    setError("");
    try {
      const job = await createOrganizationJob(organization.id, payload);
      router.push(`/recruiter/jobs/${job.id}?org=${organization.id}`);
    } catch {
      setError("Unable to create job. Check entitlement and required fields.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-4">
      {error && <div className="alert-error">{error}</div>}
      <JobForm submitting={submitting} onSubmit={submit} />
    </div>
  );
}

export default function NewRecruiterJobPage() {
  return (
    <RecruiterShell title="Create job" description="Create a draft job for your organization. Publish when it is ready.">
      <NewJobContent />
    </RecruiterShell>
  );
}
