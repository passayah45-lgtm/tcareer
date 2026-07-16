"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import { getReviewerDashboard } from "@/lib/api/courses.api";
import type { ReviewerDashboard } from "@/types/course.types";

export default function ReviewerDashboardPage() {
  const [dashboard, setDashboard] = useState<ReviewerDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const timer = window.setTimeout(() => {
      getReviewerDashboard()
        .then(setDashboard)
        .catch(() => setError("You do not have access to the reviewer workspace."))
        .finally(() => setLoading(false));
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  return (
    <>
      <Navbar />
      <main className="max-w-6xl mx-auto px-4 py-8 space-y-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold text-primary">Academic review</p>
            <h1 className="text-2xl md:text-3xl font-bold">Reviewer dashboard</h1>
            <p className="text-sm text-muted-foreground mt-1">Assignments, SLA status, workload, and governance actions.</p>
          </div>
          <Link className="btn-base btn-primary" href="/reviewer/queue">Open queue</Link>
        </div>

        {loading ? (
          <div className="h-40 rounded-xl bg-muted animate-pulse" />
        ) : error ? (
          <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-700">{error}</div>
        ) : dashboard ? (
          <div className="grid gap-4 md:grid-cols-3">
            {[
              ["Total assignments", dashboard.metrics.total],
              ["Completed", dashboard.metrics.completed],
              ["Overdue", dashboard.metrics.overdue],
              ["Approval rate", `${dashboard.metrics.approval_rate}%`],
              ["Changes requested", dashboard.metrics.changes_requested],
              ["Rejected", dashboard.metrics.rejected],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl border border-border bg-card p-5">
                <p className="text-2xl font-bold text-primary">{value}</p>
                <p className="text-sm text-muted-foreground mt-1">{label}</p>
              </div>
            ))}
          </div>
        ) : null}
      </main>
    </>
  );
}
