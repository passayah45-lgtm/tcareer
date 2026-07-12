"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { RecruiterShell, EmptyState, useRecruiterContext } from "@/components/recruiter/RecruiterShell";
import { getRecruiterDashboard } from "@/lib/api/recruiter.api";
import type { RecruiterDashboard } from "@/types/recruiter.types";

const STAGE_LABELS: Record<string, string> = {
  applied: "Applied",
  under_review: "Under Review",
  shortlisted: "Shortlisted",
  assessment: "Assessment",
  interview_scheduled: "Interview Scheduled",
  interview_completed: "Interview Completed",
  offer_sent: "Offer Sent",
  offer_accepted: "Offer Accepted",
  offer_declined: "Offer Declined",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
};

function StatCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="bg-card border border-border rounded-xl p-5">
      <p className="text-2xl font-bold text-primary">{value}</p>
      <p className="text-sm text-muted-foreground mt-1">{label}</p>
    </div>
  );
}

function BarMetric({ label, value, max }: { label: string; value: number; max: number }) {
  const pct = max ? Math.max(4, Math.round((value / max) * 100)) : 0;
  return (
    <div>
      <div className="flex items-center justify-between text-sm mb-1">
        <span>{label}</span>
        <span className="text-muted-foreground">{value}</span>
      </div>
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div className="h-full bg-primary rounded-full" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function DashboardContent() {
  const { organization } = useRecruiterContext();
  const [dashboard, setDashboard] = useState<RecruiterDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!organization) return;
    setLoading(true);
    try {
      setDashboard(await getRecruiterDashboard(organization.id));
      setError("");
    } catch {
      setError("Unable to load recruiter dashboard.");
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

  if (loading) {
    return <div className="h-64 bg-muted rounded-xl animate-pulse" />;
  }

  if (error) {
    return <EmptyState title="Dashboard unavailable" body={error} />;
  }

  if (!dashboard || !organization) {
    return <EmptyState title="No dashboard data" body="Create or publish jobs to start filling this dashboard." />;
  }

  const maxSeats = dashboard.seat_usage.max_recruiter_seats || 0;
  const activeSeats = dashboard.seat_usage.active_recruiter_seats || 0;
  const seatLabel = maxSeats ? `${activeSeats}/${maxSeats}` : activeSeats;
  const unlockLimit = dashboard.candidate_unlock_usage.limit;
  const unlockLabel = unlockLimit === null ? `${dashboard.candidate_unlock_usage.used}` : `${dashboard.candidate_unlock_usage.used}/${unlockLimit}`;
  const maxJobStatus = Math.max(dashboard.published_jobs, dashboard.draft_jobs, dashboard.archived_jobs, 1);
  const offerFunnel = [
    { label: "Interview scheduled", value: dashboard.applications_by_stage.interview_scheduled || 0 },
    { label: "Interview completed", value: dashboard.applications_by_stage.interview_completed || 0 },
    { label: "Offer sent", value: dashboard.applications_by_stage.offer_sent || 0 },
    { label: "Offer accepted", value: dashboard.applications_by_stage.offer_accepted || 0 },
  ];
  const maxOffer = Math.max(...offerFunnel.map((item) => item.value), 1);
  const activityBuckets = new Map<string, number>();
  dashboard.recent_recruiter_activity.forEach((item) => {
    const label = new Date(item.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric" });
    activityBuckets.set(label, (activityBuckets.get(label) || 0) + 1);
  });
  const activityTrend = Array.from(activityBuckets.entries()).slice(0, 7).map(([label, value]) => ({ label, value }));
  const maxActivity = Math.max(...activityTrend.map((item) => item.value), 1);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total jobs" value={dashboard.total_jobs} />
        <StatCard label="Published jobs" value={dashboard.published_jobs} />
        <StatCard label="Draft jobs" value={dashboard.draft_jobs} />
        <StatCard label="Archived jobs" value={dashboard.archived_jobs} />
        <StatCard label="Applications" value={dashboard.applications_received} />
        <StatCard label="Upcoming interviews" value={dashboard.upcoming_interviews} />
        <StatCard label="Recruiter seats" value={seatLabel} />
        <StatCard label="Candidate unlocks" value={unlockLabel} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section className="lg:col-span-2 border border-border rounded-xl bg-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Applications by stage</h2>
            <Link href={`/recruiter/pipeline?org=${organization.id}`} className="text-sm text-primary hover:underline">Open pipeline</Link>
          </div>
          <div className="space-y-3">
            {Object.entries(STAGE_LABELS).map(([stage, label]) => {
              const count = dashboard.applications_by_stage[stage] || 0;
              const pct = dashboard.applications_received ? Math.round((count / dashboard.applications_received) * 100) : 0;
              return (
                <div key={stage}>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span>{label}</span>
                    <span className="text-muted-foreground">{count}</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div className="h-full bg-primary rounded-full" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <section className="border border-border rounded-xl bg-card p-5">
          <h2 className="font-semibold mb-4">Recent activity</h2>
          {dashboard.recent_recruiter_activity.length === 0 ? (
            <p className="text-sm text-muted-foreground">No recruiter activity yet.</p>
          ) : (
            <div className="space-y-3">
              {dashboard.recent_recruiter_activity.slice(0, 8).map((item) => (
                <div key={item.id} className="border-b border-border last:border-0 pb-3 last:pb-0">
                  <p className="text-sm font-medium">{item.activity_type.replaceAll("_", " ")}</p>
                  <p className="text-xs text-muted-foreground">
                    {item.actor__full_name || "System"} - {new Date(item.created_at).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      <section className="border border-border rounded-xl bg-card p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs uppercase text-muted-foreground">AI Recruiter Copilot</p>
            <h2 className="font-semibold">Rank candidates, improve job quality, and find pipeline bottlenecks</h2>
            <p className="mt-2 text-sm text-muted-foreground">AI reports include confidence, explainability, fairness warnings, and advisory-only hiring disclaimers.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href="/ai/recruiter" className="btn-base btn-primary">Open copilot</Link>
            <Link href="/ai/recruiter/candidates" className="btn-base btn-secondary">Candidate ranking</Link>
            <Link href="/ai/recruiter/jobs" className="btn-base btn-secondary">Job analysis</Link>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        <section className="border border-border rounded-xl bg-card p-5">
          <h2 className="font-semibold mb-4">Jobs by status</h2>
          <div className="space-y-3">
            <BarMetric label="Published" value={dashboard.published_jobs} max={maxJobStatus} />
            <BarMetric label="Draft" value={dashboard.draft_jobs} max={maxJobStatus} />
            <BarMetric label="Archived" value={dashboard.archived_jobs} max={maxJobStatus} />
          </div>
        </section>

        <section className="border border-border rounded-xl bg-card p-5">
          <h2 className="font-semibold mb-4">Offer funnel</h2>
          <div className="space-y-3">
            {offerFunnel.map((item) => <BarMetric key={item.label} label={item.label} value={item.value} max={maxOffer} />)}
          </div>
        </section>

        <section className="border border-border rounded-xl bg-card p-5">
          <h2 className="font-semibold mb-4">Candidate unlock usage</h2>
          <div className="space-y-4">
            <div>
              <p className="text-3xl font-bold text-primary">{unlockLabel}</p>
              <p className="text-sm text-muted-foreground">Used candidate unlocks</p>
            </div>
            {unlockLimit !== null && <BarMetric label="Usage" value={dashboard.candidate_unlock_usage.used} max={unlockLimit || 1} />}
          </div>
        </section>

        <section className="border border-border rounded-xl bg-card p-5 md:col-span-2 xl:col-span-3">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Applications and activity over time</h2>
            <span className="text-xs text-muted-foreground">Recent recruiter events</span>
          </div>
          {activityTrend.length === 0 ? (
            <p className="text-sm text-muted-foreground">No activity trend yet.</p>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
              {activityTrend.map((item) => (
                <div key={item.label} className="bg-muted/50 rounded-lg p-3">
                  <div className="h-20 flex items-end">
                    <div className="w-full bg-primary rounded-t" style={{ height: `${Math.max(8, Math.round((item.value / maxActivity) * 80))}px` }} />
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">{item.label}</p>
                  <p className="text-sm font-medium">{item.value}</p>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

export default function RecruiterDashboardPage() {
  return (
    <RecruiterShell title="Recruiter dashboard" description="Hiring activity, seats, applications, and upcoming interviews.">
      <DashboardContent />
    </RecruiterShell>
  );
}
