"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { generateRecruiterPipelineInsights, getRecruiterAIAnalytics, getRecruiterAIHistory } from "@/lib/api/ai.api";
import type { AIRecruiterAnalytics, AIRecruiterReport } from "@/types/ai.types";

function ReportCard({ report }: { report: AIRecruiterReport }) {
  return (
    <article className="card p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase text-muted-foreground">{report.report_type.replaceAll("_", " ")}</p>
          <h3 className="mt-1 text-base font-semibold">{report.title || "Recruiter AI report"}</h3>
        </div>
        <span className="text-sm font-semibold text-primary">{report.score}/100</span>
      </div>
      <p className="mt-3 line-clamp-3 text-sm text-muted-foreground">{String(report.report.summary ?? report.fairness_notes)}</p>
    </article>
  );
}

export default function AIRecruiterPage() {
  const [analytics, setAnalytics] = useState<AIRecruiterAnalytics | null>(null);
  const [history, setHistory] = useState<AIRecruiterReport[]>([]);
  const [organizationId, setOrganizationId] = useState("");
  const [latest, setLatest] = useState<AIRecruiterReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    const [analyticsData, historyData] = await Promise.all([getRecruiterAIAnalytics(), getRecruiterAIHistory()]);
    setAnalytics(analyticsData);
    setHistory(historyData);
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      load().catch(() => setError("Unable to load recruiter copilot."));
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  async function runPipelineInsights() {
    if (!organizationId.trim()) {
      setError("Enter an organization ID first.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const report = await generateRecruiterPipelineInsights({ organization_id: organizationId.trim() });
      setLatest(report);
      await load();
    } catch {
      setError("Unable to generate pipeline insights.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">AI Recruiter Copilot</h1>
            <p className="text-sm text-muted-foreground">Candidate intelligence, ranking, job quality, interview planning, and pipeline recommendations.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href="/ai/recruiter/candidates" className="btn-base btn-primary">Candidate tools</Link>
            <Link href="/ai/recruiter/jobs" className="btn-base btn-secondary">Job tools</Link>
            <Link href="/ai/recruiter/history" className="btn-base btn-secondary">History</Link>
          </div>
        </header>

        {error && <div className="rounded-lg border border-destructive/30 bg-card p-4 text-sm text-destructive">{error}</div>}

        <section className="grid gap-4 sm:grid-cols-4">
          <div className="stat-card"><span className="stat-value">{analytics?.reports ?? 0}</span><span className="stat-label">Reports</span></div>
          <div className="stat-card"><span className="stat-value">{analytics?.average_score ?? "0.00"}</span><span className="stat-label">Average score</span></div>
          <div className="stat-card"><span className="stat-value">{analytics?.average_confidence ?? "0.00"}</span><span className="stat-label">Confidence</span></div>
          <div className="stat-card"><span className="stat-value">${analytics?.estimated_cost ?? "0.000000"}</span><span className="stat-label">AI cost</span></div>
        </section>

        <section className="card p-5">
          <h2 className="font-semibold">Pipeline insights</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto]">
            <input className="input" value={organizationId} onChange={(event) => setOrganizationId(event.target.value)} placeholder="Organization ID" />
            <button className="btn-base btn-primary" disabled={busy} onClick={() => void runPipelineInsights()}>
              {busy ? "Generating..." : "Generate insights"}
            </button>
          </div>
          {latest && (
            <div className="mt-4 rounded-lg border border-border bg-muted/30 p-4">
              <p className="text-sm font-medium">{latest.title}</p>
              <p className="mt-2 text-sm text-muted-foreground">{String(latest.report.summary ?? latest.report.pipeline_health ?? "")}</p>
            </div>
          )}
        </section>

        <section className="grid gap-4 lg:grid-cols-3">
          {history.slice(0, 6).map((report) => <ReportCard key={report.id} report={report} />)}
          {history.length === 0 && <div className="card p-5 text-sm text-muted-foreground lg:col-span-3">No recruiter AI reports yet.</div>}
        </section>
      </div>
    </main>
  );
}
