"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { Navbar } from "@/components/layout/Navbar";
import { getDashboardPathForUser } from "@/lib/auth/role-redirects";
import { getPlatformManagementDashboard } from "@/lib/api/platform.api";
import { useAuthStore } from "@/stores/auth.store";
import type { PlatformManagementDashboard } from "@/types/platform.types";
import type { UserRole } from "@/types/user.types";

const PLATFORM_ADMIN_ROLES = new Set<UserRole>(["admin", "platform_admin", "super_admin"]);

function cardTone(tone: "default" | "warning" | "success" = "default") {
  if (tone === "warning") return "text-amber-600";
  if (tone === "success") return "text-emerald-600";
  return "text-primary";
}

function StatCard({
  label,
  value,
  href,
  tone = "default",
}: {
  label: string;
  value: string | number;
  href: string;
  tone?: "default" | "warning" | "success";
}) {
  return (
    <Link href={href} className="stat-card block transition hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-sm">
      <span className={`stat-value ${cardTone(tone)}`}>{value}</span>
      <span className="stat-label">{label}</span>
    </Link>
  );
}

function DomainCard({
  title,
  href,
  metrics,
}: {
  title: string;
  href: string;
  metrics: Array<[string, string | number]>;
}) {
  return (
    <Link href={href} className="rounded-xl border border-border bg-card p-5 transition hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="font-semibold">{title}</h2>
        <span className="text-xs font-medium text-primary">Open</span>
      </div>
      <div className="space-y-3">
        {metrics.map(([label, value]) => (
          <div key={label} className="flex items-center justify-between gap-4 text-sm">
            <span className="text-muted-foreground">{label}</span>
            <strong className="text-foreground">{value}</strong>
          </div>
        ))}
      </div>
    </Link>
  );
}

function AuditActivityCard({ dashboard }: { dashboard: PlatformManagementDashboard }) {
  return (
    <Link href="/platform/audit" className="rounded-xl border border-border bg-card p-5 transition hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold">Recent platform audit activity</h2>
          <p className="mt-1 text-xs text-muted-foreground">Privileged actions and security-sensitive changes.</p>
        </div>
        <span className="text-xs font-medium text-primary">Open</span>
      </div>
      {dashboard.recent_activity.length === 0 ? (
        <p className="text-sm text-muted-foreground">No audit activity yet.</p>
      ) : (
        <div className="space-y-3">
          {dashboard.recent_activity.slice(0, 4).map((item) => (
            <div key={item.id} className="rounded-lg bg-muted/50 px-3 py-2 text-sm">
              <p className="truncate font-medium">{item.action.replaceAll("_", " ")}</p>
              <p className="mt-1 truncate text-xs text-muted-foreground">
                {item.target_type || "system"} {item.created_at ? new Date(item.created_at).toLocaleString() : ""}
              </p>
            </div>
          ))}
        </div>
      )}
    </Link>
  );
}

export default function PlatformDashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuthStore();
  const [dashboard, setDashboard] = useState<PlatformManagementDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const canAccessPlatform = Boolean(user?.role && PLATFORM_ADMIN_ROLES.has(user.role));

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.push("/login?next=/platform/dashboard");
      return;
    }
    if (!canAccessPlatform) {
      router.push(getDashboardPathForUser(user));
    }
  }, [canAccessPlatform, isAuthenticated, isLoading, router, user]);

  useEffect(() => {
    if (isLoading || !isAuthenticated || !canAccessPlatform) return;
    const timer = window.setTimeout(() => {
      setLoading(true);
      getPlatformManagementDashboard()
        .then((data) => {
          setDashboard(data);
          setError("");
        })
        .catch(() => setError("Unable to load platform management dashboard."))
        .finally(() => setLoading(false));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [canAccessPlatform, isAuthenticated, isLoading]);

  if (isLoading || (!isAuthenticated || !canAccessPlatform)) {
    return (
      <>
        <Navbar />
        <main className="min-h-[60vh] flex items-center justify-center px-4">
          <div className="w-7 h-7 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </main>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-medium text-primary">Platform management</p>
            <h1 className="text-2xl md:text-3xl font-bold mt-1">T-Career control center</h1>
            <p className="text-sm text-muted-foreground mt-2 max-w-3xl">
              Super-admin overview for learning, career marketplace, organizations, trust, AI, notifications, revenue, and platform operations.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={() => router.back()} className="btn-base btn-secondary">
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              Back
            </button>
            <Link href="/platform/operations" className="btn-base btn-primary">Operations queues</Link>
            <Link href="/platform/verification" className="btn-base btn-secondary">Verification</Link>
            <Link href="/platform/audit" className="btn-base btn-secondary">Audit search</Link>
          </div>
        </div>

        {loading && <div className="h-72 rounded-xl bg-muted animate-pulse" />}
        {error && <div className="rounded-xl border border-destructive/30 bg-card p-5 text-sm text-destructive">{error}</div>}

        {dashboard && (
          <>
            <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
              <StatCard label="Users" value={dashboard.summary.users} href="/platform/operations" />
              <StatCard label="Organizations" value={dashboard.summary.organizations} href="/organization/dashboard" />
              <StatCard label="Published courses" value={dashboard.summary.published_courses} href="/courses" />
              <StatCard label="Active jobs" value={dashboard.summary.active_jobs} href="/recruiter/jobs" />
              <StatCard
                label="Pending verification"
                value={dashboard.summary.pending_verifications}
                href="/platform/verification"
                tone={dashboard.summary.pending_verifications ? "warning" : "success"}
              />
            </section>

            <section className="rounded-xl border border-border bg-card p-5">
              <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                <div>
                  <h2 className="font-semibold">Management areas</h2>
                  <p className="text-sm text-muted-foreground mt-1">Open a focused admin surface instead of working from crowded dashboard widgets.</p>
                </div>
              </div>
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4 mt-4">
                {dashboard.sections.map((section) => (
                  <Link key={section.label} href={section.href} className="rounded-xl border border-border bg-background p-4 transition hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-sm">
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm font-semibold">{section.label}</p>
                      <span className="text-xs font-medium text-primary">Open</span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-2 leading-5">{section.description}</p>
                  </Link>
                ))}
              </div>
            </section>

            <div className="grid gap-4 lg:grid-cols-3">
              <DomainCard
                title="Learning operations"
                href="/instructor/dashboard"
                metrics={[
                  ["Courses", dashboard.learning.courses],
                  ["Draft courses", dashboard.learning.draft_courses],
                  ["Published lessons", dashboard.learning.published_lessons],
                  ["Active enrollments", dashboard.learning.active_enrollments],
                  ["Completed enrollments", dashboard.learning.completed_enrollments],
                  ["Certificates", dashboard.learning.certificates],
                ]}
              />
              <DomainCard
                title="Career marketplace"
                href="/recruiter/dashboard"
                metrics={[
                  ["Public portfolios", dashboard.career.public_portfolios as number],
                  ["Resumes", dashboard.career.resumes as number],
                  ["Jobs", dashboard.career.jobs as number],
                  ["Applications", dashboard.career.applications as number],
                  ["Recruiter waitlist", dashboard.career.recruiter_waitlist as number],
                ]}
              />
              <DomainCard
                title="Organizations and enterprise"
                href="/organization/dashboard"
                metrics={[
                  ["Active organizations", dashboard.organizations.active],
                  ["Pending organizations", dashboard.organizations.pending],
                  ["Active memberships", dashboard.organizations.memberships],
                  ["Pending invitations", dashboard.organizations.pending_invitations],
                  ["Recruiter entitlements", dashboard.organizations.recruiter_entitlements],
                  ["Queued exports", dashboard.organizations.exports_queued],
                ]}
              />
              <DomainCard
                title="Trust and verification"
                href="/platform/verification"
                metrics={[
                  ["Verification requests", dashboard.trust.verification_requests],
                  ["Submitted", dashboard.trust.submitted],
                  ["Under review", dashboard.trust.under_review],
                  ["Approved", dashboard.trust.approved],
                  ["Rejected", dashboard.trust.rejected],
                  ["Audit events 7d", dashboard.trust.audit_events_7d],
                ]}
              />
              <DomainCard
                title="AI operations"
                href="/ai/admin"
                metrics={[
                  ["Providers", dashboard.ai.providers],
                  ["Active providers", dashboard.ai.active_providers],
                  ["Requests", dashboard.ai.requests],
                  ["Requests 7d", dashboard.ai.requests_7d],
                  ["Failed 7d", dashboard.ai.failed_requests_7d],
                  ["Estimated cost", `$${dashboard.ai.estimated_cost}`],
                ]}
              />
              <DomainCard
                title="Notifications and revenue"
                href="/platform/operations"
                metrics={[
                  ["Unread notifications", dashboard.notifications.unread],
                  ["Email pending", dashboard.notifications.email_pending],
                  ["Email failed", dashboard.notifications.email_failed],
                  ["Subscriptions", dashboard.revenue.subscriptions],
                  ["Active subscriptions", dashboard.revenue.active_subscriptions],
                  ["Past due", dashboard.revenue.past_due],
                ]}
              />
              <AuditActivityCard dashboard={dashboard} />
            </div>
          </>
        )}
      </main>
    </>
  );
}
