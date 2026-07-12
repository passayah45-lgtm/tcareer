"use client";

import { useEffect, useState } from "react";
import { OrganizationShell, OrgEmptyState, useOrganizationContext } from "@/components/organization/OrganizationShell";
import { getEnterpriseDashboard } from "@/lib/api/organizations.api";
import type { EnterpriseDashboard } from "@/types/organization.types";

function Meter({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-1"><span>{label}</span><strong>{value}%</strong></div>
      <div className="h-2 rounded-full bg-muted overflow-hidden"><div className="h-full bg-primary" style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }} /></div>
    </div>
  );
}

export default function OrganizationAnalyticsPage() {
  const { organization } = useOrganizationContext();
  const [dashboard, setDashboard] = useState<EnterpriseDashboard | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!organization) return;
    getEnterpriseDashboard(organization.id).then(setDashboard).catch(() => setError("Unable to load analytics."));
  }, [organization]);

  return (
    <OrganizationShell title="Analytics" description="Learning, hiring, engagement, health, and early revenue-ready signals.">
      {error && <p className="text-sm text-destructive mb-4">{error}</p>}
      {!dashboard ? <OrgEmptyState title="Loading analytics" body="Analytics cards are being loaded." /> : (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="stat-card"><span className="stat-value">{dashboard.analytics.applications_received}</span><span className="stat-label">Applications</span></div>
            <div className="stat-card"><span className="stat-value">{dashboard.analytics.hiring_success}</span><span className="stat-label">Accepted offers</span></div>
            <div className="stat-card"><span className="stat-value">{dashboard.analytics.certificates_issued}</span><span className="stat-label">Certificates</span></div>
            <div className="stat-card"><span className="stat-value">{dashboard.analytics.student_activation_rate}%</span><span className="stat-label">Activation</span></div>
          </div>
          <section className="rounded-xl border border-border bg-card p-5 space-y-5">
            <h2 className="font-semibold">Performance meters</h2>
            <Meter label="Organization health" value={dashboard.analytics.organization_health_score} />
            <Meter label="Course completion" value={dashboard.analytics.course_completion.rate} />
            <Meter label="Certificate completion" value={dashboard.analytics.certificate_completion_rate} />
            <Meter label="Placement rate" value={dashboard.analytics.placement_rate} />
          </section>
          <div className="grid gap-4 lg:grid-cols-2">
            <section className="rounded-xl border border-border bg-card p-5">
              <h2 className="font-semibold mb-4">Applications by status</h2>
              {Object.entries(dashboard.analytics.applications_by_status).map(([stage, count]) => (
                <div key={stage} className="flex justify-between py-2 text-sm border-b border-border last:border-0">
                  <span>{stage.replaceAll("_", " ")}</span><strong>{count}</strong>
                </div>
              ))}
            </section>
            <section className="rounded-xl border border-border bg-card p-5">
              <h2 className="font-semibold mb-4">Interviews by status</h2>
              {Object.entries(dashboard.analytics.interviews_by_status).map(([stage, count]) => (
                <div key={stage} className="flex justify-between py-2 text-sm border-b border-border last:border-0">
                  <span>{stage.replaceAll("_", " ")}</span><strong>{count}</strong>
                </div>
              ))}
            </section>
          </div>
          <section className="rounded-xl border border-border bg-card p-5">
            <h2 className="font-semibold mb-4">Cohort progress</h2>
            {dashboard.analytics.course_progress_by_cohort.length === 0 ? <p className="text-sm text-muted-foreground">No cohort progress yet.</p> : dashboard.analytics.course_progress_by_cohort.map((item) => (
              <Meter key={item.cohort_id} label={`${item.name} (${item.completed}/${item.total})`} value={item.rate} />
            ))}
          </section>
          <div className="grid gap-4 lg:grid-cols-2">
            <section className="rounded-xl border border-border bg-card p-5">
              <h2 className="font-semibold mb-4">Department breakdown</h2>
              {dashboard.analytics.department_breakdown.map((item) => (
                <div key={item.id} className="flex justify-between py-2 text-sm border-b border-border last:border-0"><span>{item.name}</span><strong>{item.member_count}</strong></div>
              ))}
            </section>
            <section className="rounded-xl border border-border bg-card p-5">
              <h2 className="font-semibold mb-4">Monthly trends</h2>
              {Object.entries(dashboard.analytics.monthly_trend_summary).map(([key, value]) => (
                <div key={key} className="flex justify-between py-2 text-sm border-b border-border last:border-0"><span>{key.replaceAll("_", " ")}</span><strong>{value}</strong></div>
              ))}
            </section>
          </div>
          <section className="rounded-xl border border-border bg-card p-5">
            <h2 className="font-semibold mb-4">Enterprise readiness</h2>
            <div className="grid gap-3 md:grid-cols-3 text-sm">
              <p className="rounded-lg bg-muted p-3">Members: {dashboard.hierarchy.members}</p>
              <p className="rounded-lg bg-muted p-3">Cohorts: {dashboard.hierarchy.cohorts}</p>
              <p className="rounded-lg bg-muted p-3">Revenue placeholder: {dashboard.analytics.revenue.placeholder ? "Pending billing" : dashboard.analytics.revenue.amount}</p>
            </div>
          </section>
        </div>
      )}
    </OrganizationShell>
  );
}
