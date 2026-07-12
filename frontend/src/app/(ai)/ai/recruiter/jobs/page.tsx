"use client";

import Link from "next/link";
import { useState } from "react";
import { analyzeRecruiterJob, createRecruiterInterviewPlan } from "@/lib/api/ai.api";
import type { AIRecruiterReport } from "@/types/ai.types";

export default function AIRecruiterJobsPage() {
  const [jobId, setJobId] = useState("");
  const [organizationId, setOrganizationId] = useState("");
  const [candidateId, setCandidateId] = useState("");
  const [title, setTitle] = useState("Backend Django Developer");
  const [description, setDescription] = useState("");
  const [report, setReport] = useState<AIRecruiterReport | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  async function runJobAnalysis() {
    setBusy("job");
    setError("");
    try {
      setReport(await analyzeRecruiterJob({ job_id: jobId.trim() || undefined, title, description }));
    } catch {
      setError("Unable to analyze job.");
    } finally {
      setBusy("");
    }
  }

  async function runInterviewPlan() {
    setBusy("interview");
    setError("");
    try {
      setReport(await createRecruiterInterviewPlan({ candidate_id: candidateId.trim(), organization_id: organizationId.trim() || undefined, job_id: jobId.trim() || undefined }));
    } catch {
      setError("Unable to create interview plan.");
    } finally {
      setBusy("");
    }
  }

  return (
    <main className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">AI Job Intelligence</h1>
            <p className="text-sm text-muted-foreground">Improve job descriptions and create structured interview plans for candidates.</p>
          </div>
          <Link href="/ai/recruiter" className="btn-base btn-secondary">Copilot home</Link>
        </header>

        {error && <div className="rounded-lg border border-destructive/30 bg-card p-4 text-sm text-destructive">{error}</div>}

        <section className="grid gap-6 lg:grid-cols-[0.8fr_1fr]">
          <div className="space-y-6">
            <section className="card p-5">
              <h2 className="font-semibold">Job analysis</h2>
              <div className="mt-4 space-y-3">
                <input className="input w-full" value={jobId} onChange={(event) => setJobId(event.target.value)} placeholder="Existing job ID" />
                <input className="input w-full" value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Draft job title" />
                <textarea className="input min-h-36 w-full" value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Draft job description when no job ID is available" />
                <button className="btn-base btn-primary" disabled={busy !== ""} onClick={() => void runJobAnalysis()}>{busy === "job" ? "Analyzing..." : "Analyze job"}</button>
              </div>
            </section>

            <section className="card p-5">
              <h2 className="font-semibold">Interview plan</h2>
              <div className="mt-4 space-y-3">
                <input className="input w-full" value={organizationId} onChange={(event) => setOrganizationId(event.target.value)} placeholder="Organization ID" />
                <input className="input w-full" value={candidateId} onChange={(event) => setCandidateId(event.target.value)} placeholder="Candidate ID" />
                <button className="btn-base btn-secondary" disabled={busy !== "" || !candidateId.trim()} onClick={() => void runInterviewPlan()}>{busy === "interview" ? "Planning..." : "Create plan"}</button>
              </div>
            </section>
          </div>

          <section className="card p-5">
            {!report ? (
              <p className="text-sm text-muted-foreground">Run job analysis or interview planning to see AI output.</p>
            ) : (
              <>
                <p className="text-xs uppercase text-muted-foreground">{report.report_type.replaceAll("_", " ")}</p>
                <h2 className="font-semibold">{report.title}</h2>
                <p className="mt-4 text-sm text-muted-foreground">{String(report.report.summary ?? "")}</p>
                <pre className="mt-4 max-h-96 overflow-auto rounded-lg bg-muted p-4 text-xs">{JSON.stringify(report.report, null, 2)}</pre>
                <p className="mt-4 text-xs text-muted-foreground">{report.disclaimer}</p>
              </>
            )}
          </section>
        </section>
      </div>
    </main>
  );
}
