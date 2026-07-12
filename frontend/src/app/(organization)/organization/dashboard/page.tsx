"use client";

import { useEffect, useState } from "react";
import { OrganizationShell, OrgEmptyState, useOrganizationContext } from "@/components/organization/OrganizationShell";
import { getEnterpriseDashboard } from "@/lib/api/organizations.api";
import type { EnterpriseDashboard } from "@/types/organization.types";

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="stat-card">
      <span className="stat-value">{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  );
}

export default function OrganizationDashboardPage() {
  const { organization } = useOrganizationContext();
  const [dashboard, setDashboard] = useState<EnterpriseDashboard | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!organization) return;
    const timer = window.setTimeout(() => {
      setLoading(true);
      getEnterpriseDashboard(organization.id)
        .then(setDashboard)
        .catch(() => setError("Unable to load organization dashboard."))
        .finally(() => setLoading(false));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [organization]);

  return (
    <OrganizationShell title="Organization dashboard" description="Enterprise health, hierarchy, learning, hiring, and audit overview.">
      {loading && <p className="text-sm text-muted-foreground">Loading dashboard...</p>}
      {error && <p className="text-sm text-destructive">{error}</p>}
      {!loading && !dashboard && !error && <OrgEmptyState title="No dashboard data" body="Organization metrics appear here once the API responds." />}
      {dashboard && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Active learners" value={dashboard.analytics.active_learners} />
            <StatCard label="Active recruiters" value={dashboard.analytics.active_recruiters} />
            <StatCard label="Jobs posted" value={dashboard.analytics.jobs_posted} />
            <StatCard label="Health score" value={`${dashboard.analytics.organization_health_score}%`} />
          </div>
          {!dashboard.can_manage && (
            <div className="rounded-xl border border-border bg-muted p-4 text-sm text-muted-foreground">
              You have read-only enterprise access. Management actions are hidden or denied by the API.
            </div>
          )}
          <div className="grid gap-4 lg:grid-cols-3">
            <section className="rounded-xl border border-border bg-card p-5">
              <h2 className="font-semibold mb-4">Hierarchy</h2>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between"><span>Departments</span><strong>{dashboard.hierarchy.departments}</strong></div>
                <div className="flex justify-between"><span>Teams</span><strong>{dashboard.hierarchy.teams}</strong></div>
                <div className="flex justify-between"><span>Cohorts</span><strong>{dashboard.hierarchy.cohorts}</strong></div>
                <div className="flex justify-between"><span>Members</span><strong>{dashboard.hierarchy.members}</strong></div>
              </div>
            </section>
            <section className="rounded-xl border border-border bg-card p-5">
              <h2 className="font-semibold mb-4">Learning</h2>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between"><span>Course completion</span><strong>{dashboard.analytics.course_completion.rate}%</strong></div>
                <div className="flex justify-between"><span>Activation</span><strong>{dashboard.analytics.student_activation_rate}%</strong></div>
                <div className="flex justify-between"><span>Completed enrollments</span><strong>{dashboard.analytics.course_completion.completed}</strong></div>
                <div className="flex justify-between"><span>Certificates issued</span><strong>{dashboard.analytics.certificates_issued}</strong></div>
              </div>
            </section>
            <section className="rounded-xl border border-border bg-card p-5">
              <h2 className="font-semibold mb-4">Hiring</h2>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between"><span>Applications</span><strong>{dashboard.analytics.applications_received}</strong></div>
                <div className="flex justify-between"><span>Interviews</span><strong>{dashboard.analytics.interviews}</strong></div>
                <div className="flex justify-between"><span>Placement rate</span><strong>{dashboard.analytics.placement_rate}%</strong></div>
              </div>
            </section>
          </div>
          <section className="rounded-xl border border-border bg-card p-5">
            <h2 className="font-semibold mb-4">Recent audit activity</h2>
            {dashboard.recent_audit_activity.length === 0 ? (
              <p className="text-sm text-muted-foreground">No audit events yet.</p>
            ) : (
              <div className="divide-y divide-border">
                {dashboard.recent_audit_activity.map((item) => (
                  <div key={item.id} className="py-3 text-sm flex flex-col gap-1 md:flex-row md:justify-between">
                    <span>{item.action.replaceAll("_", " ")}</span>
                    <span className="text-muted-foreground">{new Date(item.created_at).toLocaleString()}</span>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </OrganizationShell>
  );
}
