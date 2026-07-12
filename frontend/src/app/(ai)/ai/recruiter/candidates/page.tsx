"use client";

import Link from "next/link";
import { useState } from "react";
import { analyzeRecruiterCandidate, compareRecruiterCandidates, rankRecruiterCandidates } from "@/lib/api/ai.api";
import type { AIRecruiterReport } from "@/types/ai.types";

function splitIds(value: string) {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function ReportView({ report }: { report: AIRecruiterReport | null }) {
  if (!report) return <div className="card p-5 text-sm text-muted-foreground">Run an analysis to see recruiter AI output.</div>;
  return (
    <section className="card p-5">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs uppercase text-muted-foreground">{report.report_type.replaceAll("_", " ")}</p>
          <h2 className="font-semibold">{report.title}</h2>
        </div>
        <div className="text-sm text-primary">{report.score}/100 confidence {report.confidence_score}</div>
      </div>
      <p className="mt-4 text-sm text-muted-foreground">{String(report.report.summary ?? report.fairness_notes)}</p>
      <pre className="mt-4 max-h-96 overflow-auto rounded-lg bg-muted p-4 text-xs">{JSON.stringify(report.report, null, 2)}</pre>
      <p className="mt-4 text-xs text-muted-foreground">{report.disclaimer}</p>
    </section>
  );
}

export default function AIRecruiterCandidatesPage() {
  const [organizationId, setOrganizationId] = useState("");
  const [jobId, setJobId] = useState("");
  const [candidateId, setCandidateId] = useState("");
  const [candidateIds, setCandidateIds] = useState("");
  const [sortBy, setSortBy] = useState<"best_fit" | "highest_confidence" | "highest_growth_potential" | "highest_learning_activity">("best_fit");
  const [report, setReport] = useState<AIRecruiterReport | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  async function run(action: "analysis" | "ranking" | "comparison") {
    setBusy(action);
    setError("");
    try {
      if (action === "analysis") {
        setReport(await analyzeRecruiterCandidate({ candidate_id: candidateId.trim(), organization_id: organizationId.trim() || undefined, job_id: jobId.trim() || undefined }));
      } else if (action === "ranking") {
        setReport(await rankRecruiterCandidates({ job_id: jobId.trim(), candidate_ids: splitIds(candidateIds), sort_by: sortBy }));
      } else {
        setReport(await compareRecruiterCandidates({ candidate_ids: splitIds(candidateIds), organization_id: organizationId.trim() || undefined, job_id: jobId.trim() || undefined }));
      }
    } catch {
      setError(`Unable to run candidate ${action}.`);
    } finally {
      setBusy("");
    }
  }

  return (
    <main className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">AI Candidate Intelligence</h1>
            <p className="text-sm text-muted-foreground">Analyze, rank, and compare candidates with fairness warnings and explainability.</p>
          </div>
          <Link href="/ai/recruiter" className="btn-base btn-secondary">Copilot home</Link>
        </header>

        {error && <div className="rounded-lg border border-destructive/30 bg-card p-4 text-sm text-destructive">{error}</div>}

        <section className="grid gap-6 lg:grid-cols-[0.8fr_1fr]">
          <div className="card p-5">
            <h2 className="font-semibold">Inputs</h2>
            <div className="mt-4 space-y-3">
              <input className="input w-full" value={organizationId} onChange={(event) => setOrganizationId(event.target.value)} placeholder="Organization ID" />
              <input className="input w-full" value={jobId} onChange={(event) => setJobId(event.target.value)} placeholder="Job ID" />
              <input className="input w-full" value={candidateId} onChange={(event) => setCandidateId(event.target.value)} placeholder="Single candidate ID" />
              <textarea className="input min-h-24 w-full" value={candidateIds} onChange={(event) => setCandidateIds(event.target.value)} placeholder="Candidate IDs for ranking/comparison, comma-separated" />
              <select className="input w-full" value={sortBy} onChange={(event) => setSortBy(event.target.value as typeof sortBy)}>
                <option value="best_fit">Best fit</option>
                <option value="highest_confidence">Highest confidence</option>
                <option value="highest_growth_potential">Highest growth potential</option>
                <option value="highest_learning_activity">Highest learning activity</option>
              </select>
              <div className="flex flex-wrap gap-2">
                <button className="btn-base btn-primary" disabled={busy !== "" || !candidateId.trim()} onClick={() => void run("analysis")}>{busy === "analysis" ? "Analyzing..." : "Analyze"}</button>
                <button className="btn-base btn-secondary" disabled={busy !== "" || !jobId.trim() || splitIds(candidateIds).length === 0} onClick={() => void run("ranking")}>Rank</button>
                <button className="btn-base btn-secondary" disabled={busy !== "" || splitIds(candidateIds).length < 2} onClick={() => void run("comparison")}>Compare</button>
              </div>
            </div>
          </div>
          <ReportView report={report} />
        </section>
      </div>
    </main>
  );
}
