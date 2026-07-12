"use client";

import { useEffect, useState } from "react";
import { bulkApproveAIReviews, getAIReviewerQueue, reviewAIResult } from "@/lib/api/ai.api";
import type { AIEvaluationReview, AIReviewerQueue } from "@/types/ai.types";

const statusOptions = ["", "pending", "manual_review", "approved", "rejected"];
const featureOptions = ["", "chat", "resume_review", "portfolio_review", "job_matching", "interview_coach"];
const datasetTypeOptions = ["", "resume_intelligence", "portfolio_intelligence", "interview_coach", "prompt_security", "privacy_dlp", "fairness", "hallucination"];

function ReviewCard({ review, onAction }: { review: AIEvaluationReview; onAction: (review: AIEvaluationReview, status: string, flags?: Partial<AIEvaluationReview>) => void }) {
  return (
    <article className="rounded-md border border-border p-4 text-sm">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="font-medium">{review.dataset_name || "Evaluation result"}</p>
          <p className="text-muted-foreground">Status {review.status} - score {review.manual_score ?? "not reviewed"}</p>
        </div>
        <span className="tag">{review.assigned_to ? "assigned" : "unassigned"}</span>
      </div>
      {review.notes && <p className="mt-3 text-muted-foreground">{review.notes}</p>}
      <div className="mt-4 flex flex-wrap gap-2">
        <button className="btn-base btn-secondary" onClick={() => onAction(review, "approved")}>Approve</button>
        <button className="btn-base btn-secondary" onClick={() => onAction(review, "rejected")}>Reject</button>
        <button className="btn-base btn-secondary" onClick={() => onAction(review, "manual_review", { hallucination_flag: true })}>Flag hallucination</button>
        <button className="btn-base btn-secondary" onClick={() => onAction(review, "manual_review", { bias_flag: true })}>Flag bias</button>
        <button className="btn-base btn-secondary" onClick={() => onAction(review, "manual_review", { unsafe_flag: true })}>Flag unsafe</button>
        <button className="btn-base btn-secondary" onClick={() => onAction(review, "manual_review", { request_prompt_revision: true })}>Request prompt revision</button>
      </div>
    </article>
  );
}

export default function AIReviewerPage() {
  const [queue, setQueue] = useState<AIReviewerQueue | null>(null);
  const [status, setStatus] = useState("");
  const [feature, setFeature] = useState("");
  const [datasetType, setDatasetType] = useState("");
  const [riskTag, setRiskTag] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function loadQueue() {
    setLoading(true);
    setError("");
    try {
      setQueue(await getAIReviewerQueue({ status, feature, dataset_type: datasetType, risk_tag: riskTag }));
    } catch {
      setError("AI reviewer access is required.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let isMounted = true;
    getAIReviewerQueue({ status, feature, dataset_type: datasetType, risk_tag: riskTag })
      .then((data) => {
        if (isMounted) setQueue(data);
      })
      .catch(() => {
        if (isMounted) setError("AI reviewer access is required.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [status, feature, datasetType, riskTag]);

  async function onAction(review: AIEvaluationReview, nextStatus: string, flags: Partial<AIEvaluationReview> = {}) {
    setMessage("");
    setError("");
    try {
      await reviewAIResult(review.result, {
        status: nextStatus,
        notes: flags.request_prompt_revision ? "Prompt revision requested from reviewer console." : "",
        hallucination_flag: Boolean(flags.hallucination_flag),
        bias_flag: Boolean(flags.bias_flag),
        unsafe_flag: Boolean(flags.unsafe_flag),
        request_prompt_revision: Boolean(flags.request_prompt_revision),
      });
      setMessage("Review updated.");
      await loadQueue();
    } catch {
      setError("Unable to update review.");
    }
  }

  async function bulkApproveAssigned() {
    const ids = queue?.assigned.map((item) => item.id) ?? [];
    if (ids.length === 0) return;
    setMessage("");
    setError("");
    try {
      await bulkApproveAIReviews(ids, "Bulk approved from reviewer console.");
      setMessage(`Approved ${ids.length} assigned review(s).`);
      await loadQueue();
    } catch {
      setError("Unable to bulk approve reviews.");
    }
  }

  return (
    <main className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">AI Reviewer Console</h1>
            <p className="text-sm text-muted-foreground">Review queue, flags, prompt revision requests, and reviewer workload.</p>
          </div>
          <button className="btn-base btn-primary" onClick={() => void bulkApproveAssigned()}>Bulk approve assigned</button>
        </header>

        {message && <p className="text-sm text-primary">{message}</p>}
        {error && <p className="text-sm text-destructive">{error}</p>}

        <section className="card p-5">
          <div className="grid gap-3 md:grid-cols-4">
            <select className="input" value={feature} onChange={(event) => setFeature(event.target.value)}>
              {featureOptions.map((item) => <option key={item} value={item}>{item || "All features"}</option>)}
            </select>
            <select className="input" value={datasetType} onChange={(event) => setDatasetType(event.target.value)}>
              {datasetTypeOptions.map((item) => <option key={item} value={item}>{item || "All dataset types"}</option>)}
            </select>
            <select className="input" value={status} onChange={(event) => setStatus(event.target.value)}>
              {statusOptions.map((item) => <option key={item} value={item}>{item || "All statuses"}</option>)}
            </select>
            <input className="input" value={riskTag} onChange={(event) => setRiskTag(event.target.value)} placeholder="Risk tag" />
          </div>
        </section>

        {loading && <div className="card p-5 text-sm text-muted-foreground">Loading reviewer queue...</div>}

        {queue && (
          <>
            <section className="grid gap-4 md:grid-cols-3">
              <div className="stat-card"><span className="stat-value">{queue.assigned.length}</span><span className="stat-label">Assigned to you</span></div>
              <div className="stat-card"><span className="stat-value">{queue.unassigned.length}</span><span className="stat-label">Unassigned</span></div>
              <div className="stat-card"><span className="stat-value">{queue.workload.length}</span><span className="stat-label">Reviewers</span></div>
            </section>

            <section className="grid gap-6 lg:grid-cols-[1fr_320px]">
              <div className="space-y-6">
                <section className="card p-5">
                  <h2 className="font-semibold">Assigned queue</h2>
                  <div className="mt-4 grid gap-3">
                    {queue.assigned.length === 0 && <p className="text-sm text-muted-foreground">No assigned reviews match the current filters.</p>}
                    {queue.assigned.map((review) => <ReviewCard key={review.id} review={review} onAction={onAction} />)}
                  </div>
                </section>
                <section className="card p-5">
                  <h2 className="font-semibold">Unassigned queue</h2>
                  <div className="mt-4 grid gap-3">
                    {queue.unassigned.length === 0 && <p className="text-sm text-muted-foreground">No unassigned reviews match the current filters.</p>}
                    {queue.unassigned.map((review) => <ReviewCard key={review.id} review={review} onAction={onAction} />)}
                  </div>
                </section>
              </div>
              <aside className="card p-5">
                <h2 className="font-semibold">Reviewer workload</h2>
                <div className="mt-4 space-y-2">
                  {queue.workload.map((item) => (
                    <div key={item.assigned_to__email ?? "unassigned"} className="rounded-md border border-border p-3 text-sm">
                      <p className="font-medium">{item.assigned_to__email ?? "Unassigned"}</p>
                      <p className="text-muted-foreground">{item.pending} pending - {item.total} total</p>
                    </div>
                  ))}
                </div>
              </aside>
            </section>
          </>
        )}
      </div>
    </main>
  );
}
