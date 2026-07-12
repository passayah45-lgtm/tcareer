"use client";

import { useEffect, useState } from "react";
import { getAIQualityDashboard } from "@/lib/api/ai.api";
import type { AIQualityDashboard } from "@/types/ai.types";

function Percent({ value }: { value: number }) {
  return <span>{Math.round(value * 100)}%</span>;
}

export default function AIQualityPage() {
  const [quality, setQuality] = useState<AIQualityDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getAIQualityDashboard()
      .then(setQuality)
      .catch(() => setError("Unable to load AI quality dashboard."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header>
          <h1 className="text-2xl font-semibold">AI Quality</h1>
          <p className="text-sm text-muted-foreground">Evaluation history, confidence trends, bias/privacy monitoring, feedback, provider comparison, and cache efficiency.</p>
        </header>

        {loading && <div className="card p-5 text-sm text-muted-foreground">Loading AI quality signals...</div>}
        {error && <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

        {quality && (
          <>
            <section className="grid gap-4 sm:grid-cols-4">
              <div className="stat-card"><span className="stat-value">{quality.request_count}</span><span className="stat-label">AI requests</span></div>
              <div className="stat-card"><span className="stat-value"><Percent value={quality.failure_rate} /></span><span className="stat-label">Failure rate</span></div>
              <div className="stat-card"><span className="stat-value">${quality.estimated_cost}</span><span className="stat-label">Estimated cost</span></div>
              <div className="stat-card"><span className="stat-value"><Percent value={quality.cache.cache_hit_ratio} /></span><span className="stat-label">Cache hit ratio</span></div>
            </section>

            <section className="grid gap-6 lg:grid-cols-2">
              <div className="card p-5">
                <h2 className="font-semibold">Feature quality</h2>
                <div className="mt-4 space-y-2">
                  {quality.feature_quality.length === 0 && <p className="text-sm text-muted-foreground">No evaluation runs yet.</p>}
                  {quality.feature_quality.map((item) => (
                    <div key={item.dataset__feature} className="flex items-center justify-between rounded-md border px-3 py-2 text-sm">
                      <span>{item.dataset__feature.replaceAll("_", " ")}</span>
                      <span className="font-medium">score {item.avg_score ?? "n/a"} - confidence {item.avg_confidence ?? "n/a"}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="card p-5">
                <h2 className="font-semibold">Safety reports</h2>
                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                  <div className="rounded-md border p-3"><strong className="block text-xl text-primary">{quality.bias_reports.total}</strong><span className="text-sm text-muted-foreground">Bias reports</span></div>
                  <div className="rounded-md border p-3"><strong className="block text-xl text-primary">{quality.bias_reports.manual_review}</strong><span className="text-sm text-muted-foreground">Manual reviews</span></div>
                  <div className="rounded-md border p-3"><strong className="block text-xl text-primary">{quality.privacy_reports.high}</strong><span className="text-sm text-muted-foreground">High privacy</span></div>
                </div>
              </div>
            </section>

            <section className="grid gap-6 lg:grid-cols-2">
              <div className="card p-5">
                <h2 className="font-semibold">Provider comparison</h2>
                <div className="mt-4 space-y-2">
                  {quality.provider_comparison.map((item) => (
                    <div key={`${item.provider__provider_type}-${item.model_configuration__model_name}`} className="flex items-center justify-between rounded-md border px-3 py-2 text-sm">
                      <span>{item.provider__provider_type ?? "unknown"} / {item.model_configuration__model_name ?? "unknown"}</span>
                      <span>{item.total} requests - {Math.round(item.avg_latency_ms ?? 0)}ms</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="card p-5">
                <h2 className="font-semibold">User feedback</h2>
                <div className="mt-4 flex flex-wrap gap-2">
                  {quality.feedback.by_rating.length === 0 && <p className="text-sm text-muted-foreground">No AI feedback yet.</p>}
                  {quality.feedback.by_rating.map((item) => (
                    <span key={item.rating} className="tag">{item.rating.replaceAll("_", " ")}: {item.total}</span>
                  ))}
                </div>
              </div>
            </section>

            <section className="grid gap-6 lg:grid-cols-2">
              <div className="card p-5">
                <h2 className="font-semibold">Reviewer queue</h2>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-md border p-3"><strong className="block text-xl text-primary">{quality.reviewer_queue.pending}</strong><span className="text-sm text-muted-foreground">Pending</span></div>
                  <div className="rounded-md border p-3"><strong className="block text-xl text-primary">{quality.reviewer_queue.manual_review}</strong><span className="text-sm text-muted-foreground">Manual review</span></div>
                </div>
                <div className="mt-4 space-y-2">
                  {quality.reviewer_queue.recent.map((item) => (
                    <div key={item.id} className="rounded-md border px-3 py-2 text-sm">
                      <span className="font-medium">{item.status}</span>
                      <span className="ml-2 text-muted-foreground">hallucination {item.hallucination_flag ? "yes" : "no"} - bias {item.bias_flag ? "yes" : "no"}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="card p-5">
                <h2 className="font-semibold">Red-team testing</h2>
                <div className="mt-4 grid gap-3 sm:grid-cols-4">
                  <div className="rounded-md border p-3"><strong className="block text-xl text-primary">{quality.red_team.suites}</strong><span className="text-sm text-muted-foreground">Suites</span></div>
                  <div className="rounded-md border p-3"><strong className="block text-xl text-primary">{quality.red_team.results}</strong><span className="text-sm text-muted-foreground">Results</span></div>
                  <div className="rounded-md border p-3"><strong className="block text-xl text-primary">{quality.red_team.failed}</strong><span className="text-sm text-muted-foreground">Failed</span></div>
                  <div className="rounded-md border p-3"><strong className="block text-xl text-primary">{quality.red_team.high_risk}</strong><span className="text-sm text-muted-foreground">High risk</span></div>
                </div>
              </div>
            </section>

            <section className="grid gap-6 lg:grid-cols-2">
              <div className="card p-5">
                <h2 className="font-semibold">Comparison reports</h2>
                <div className="mt-4 space-y-2">
                  {quality.comparisons.length === 0 && <p className="text-sm text-muted-foreground">No comparison reports yet.</p>}
                  {quality.comparisons.map((item) => (
                    <div key={item.id} className="rounded-md border px-3 py-2 text-sm">
                      <p className="font-medium">{item.comparison_type} - {item.feature}</p>
                      <p className="text-muted-foreground">{item.left_label} vs {item.right_label} - winner {item.winner || "n/a"}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="card p-5">
                <h2 className="font-semibold">AI audit exports</h2>
                <div className="mt-4 space-y-2">
                  {quality.audit_exports.length === 0 && <p className="text-sm text-muted-foreground">No exports yet.</p>}
                  {quality.audit_exports.map((item) => (
                    <div key={item.id} className="rounded-md border px-3 py-2 text-sm">
                      <p className="font-medium">{item.export_type.replaceAll("_", " ")} - {item.status}</p>
                      <p className="text-muted-foreground">{item.file_format.toUpperCase()} - {item.row_count} rows</p>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="card p-5">
              <h2 className="font-semibold">Evaluation history</h2>
              <div className="mt-4 grid gap-3">
                {quality.evaluation_history.length === 0 && <p className="text-sm text-muted-foreground">No evaluation history yet.</p>}
                {quality.evaluation_history.map((run) => (
                  <div key={run.id} className="rounded-md border p-3 text-sm">
                    <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                      <span className="font-medium">{run.dataset__name}</span>
                      <span className="text-muted-foreground">{run.status} - {run.dataset__feature}</span>
                    </div>
                    <p className="mt-1 text-muted-foreground">Score {run.average_score ?? "n/a"} - Confidence {run.confidence_score ?? "n/a"} - Cost ${run.estimated_cost}</p>
                  </div>
                ))}
              </div>
            </section>
          </>
        )}
      </div>
    </main>
  );
}
