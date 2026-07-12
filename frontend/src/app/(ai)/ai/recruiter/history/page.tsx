"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getRecruiterAIAnalytics, getRecruiterAIHistory } from "@/lib/api/ai.api";
import type { AIRecruiterAnalytics, AIRecruiterReport } from "@/types/ai.types";

export default function AIRecruiterHistoryPage() {
  const [reports, setReports] = useState<AIRecruiterReport[]>([]);
  const [analytics, setAnalytics] = useState<AIRecruiterAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getRecruiterAIHistory(), getRecruiterAIAnalytics()])
      .then(([historyData, analyticsData]) => {
        setReports(historyData);
        setAnalytics(analyticsData);
      })
      .catch(() => setError("Unable to load recruiter AI history."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Recruiter AI history</h1>
            <p className="text-sm text-muted-foreground">Saved candidate analysis, rankings, comparisons, job reports, interview plans, and pipeline insights.</p>
          </div>
          <Link href="/ai/recruiter" className="btn-base btn-secondary">Copilot home</Link>
        </header>

        {error && <div className="rounded-lg border border-destructive/30 bg-card p-4 text-sm text-destructive">{error}</div>}
        {loading && <div className="card p-5 text-sm text-muted-foreground">Loading recruiter AI history...</div>}

        <section className="grid gap-4 sm:grid-cols-4">
          <div className="stat-card"><span className="stat-value">{analytics?.reports ?? 0}</span><span className="stat-label">Reports</span></div>
          <div className="stat-card"><span className="stat-value">{analytics?.average_score ?? "0.00"}</span><span className="stat-label">Average score</span></div>
          <div className="stat-card"><span className="stat-value">{analytics?.average_confidence ?? "0.00"}</span><span className="stat-label">Confidence</span></div>
          <div className="stat-card"><span className="stat-value">${analytics?.estimated_cost ?? "0.000000"}</span><span className="stat-label">Cost</span></div>
        </section>

        <section className="card p-5">
          <h2 className="font-semibold">Reports</h2>
          <div className="mt-4 divide-y divide-border">
            {!loading && reports.length === 0 && <p className="text-sm text-muted-foreground">No recruiter AI reports yet.</p>}
            {reports.map((report) => (
              <article key={report.id} className="py-4 first:pt-0 last:pb-0">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="text-xs uppercase text-muted-foreground">{report.report_type.replaceAll("_", " ")}</p>
                    <h3 className="font-semibold">{report.title}</h3>
                    <p className="text-sm text-muted-foreground">{new Date(report.created_at).toLocaleString()}</p>
                  </div>
                  <span className="text-sm text-primary">{report.score}/100</span>
                </div>
                <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">{String(report.report.summary ?? report.fairness_notes)}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
