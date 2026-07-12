"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { useAuthStore } from "@/stores/auth.store";
import { getStudentDashboard, trackRecommendedJobClick } from "@/lib/api/student-career.api";
import { getDashboardPathForUser } from "@/lib/auth/role-redirects";
import type { StudentDashboard } from "@/types/student-career.types";

function CompletionCard({ label, value, href }: { label: string; value: number; href: string }) {
  return (
    <Link href={href} className="border border-border rounded-xl bg-card p-5 hover:shadow-sm transition-all">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-medium">{label}</p>
        <span className="text-sm font-semibold text-primary">{value}%</span>
      </div>
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div className="h-full bg-primary rounded-full" style={{ width: `${value}%` }} />
      </div>
    </Link>
  );
}

function Empty({ title, body }: { title: string; body: string }) {
  return (
    <div className="border border-border rounded-xl bg-card p-8 text-center">
      <p className="font-medium text-sm">{title}</p>
      <p className="text-xs text-muted-foreground mt-1">{body}</p>
    </div>
  );
}

export default function StudentDashboard() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuthStore();
  const [dashboard, setDashboard] = useState<StudentDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.push("/login?next=/dashboard");
      return;
    }
    if (user?.role !== "student") {
      router.push(getDashboardPathForUser(user));
      return;
    }
    setLoading(true);
    try {
      setDashboard(await getStudentDashboard());
      setError("");
    } catch {
      setError("Unable to load student dashboard.");
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, isLoading, router, user]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  return (
    <>
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 py-8 space-y-8">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold">Career dashboard</h1>
            <p className="text-sm text-muted-foreground mt-1">Welcome back, {user?.full_name?.split(" ")[0] || "student"}. Track your learning, profile, applications, and opportunities.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href="/jobs" className="btn-base btn-primary">Find jobs</Link>
            <Link href="/career-profile" className="btn-base btn-secondary">Career profile</Link>
          </div>
        </div>

        {loading && <div className="h-72 bg-muted rounded-xl animate-pulse" />}
        {error && <Empty title="Dashboard unavailable" body={error} />}

        {dashboard && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <CompletionCard label="Profile completion" value={dashboard.profile_completion} href="/career-profile" />
              <CompletionCard label="Resume completion" value={dashboard.resume_completion} href="/resumes" />
              <CompletionCard label="Portfolio completion" value={dashboard.portfolio_completion} href="/portfolio" />
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="stat-card"><span className="stat-value">{dashboard.skills_summary.length}</span><span className="stat-label">Skills</span></div>
              <div className="stat-card"><span className="stat-value">{dashboard.certificates_earned}</span><span className="stat-label">Certificates</span></div>
              <div className="stat-card"><span className="stat-value">{dashboard.applications_submitted}</span><span className="stat-label">Applications</span></div>
              <div className="stat-card"><span className="stat-value">{dashboard.upcoming_interviews.length}</span><span className="stat-label">Upcoming interviews</span></div>
            </div>

            <section className="border border-border rounded-xl bg-card p-5">
              <h2 className="font-semibold mb-4">Career analytics</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="stat-card"><span className="stat-value">{dashboard.student_analytics.profile_views}</span><span className="stat-label">Profile views</span></div>
                <div className="stat-card"><span className="stat-value">{dashboard.student_analytics.recruiter_views}</span><span className="stat-label">Recruiter views</span></div>
                <div className="stat-card"><span className="stat-value">{dashboard.student_analytics.resume_downloads}</span><span className="stat-label">Resume downloads</span></div>
                <div className="stat-card"><span className="stat-value">{dashboard.student_analytics.portfolio_views}</span><span className="stat-label">Portfolio views</span></div>
                <div className="stat-card"><span className="stat-value">{dashboard.student_analytics.saved_jobs}</span><span className="stat-label">Saved jobs</span></div>
                <div className="stat-card"><span className="stat-value">{dashboard.student_analytics.job_alert_matches}</span><span className="stat-label">Alert matches</span></div>
                <div className="stat-card"><span className="stat-value">{dashboard.student_analytics.recommended_job_clicks}</span><span className="stat-label">Recommendation clicks</span></div>
                <div className="stat-card"><span className="stat-value">{Object.values(dashboard.student_analytics.applications_by_status).reduce((sum, count) => sum + count, 0)}</span><span className="stat-label">Tracked applications</span></div>
              </div>
              <div className="flex flex-wrap gap-2 mt-4">
                {Object.entries(dashboard.student_analytics.applications_by_status).map(([stage, count]) => (
                  <span key={stage} className="tag">{stage.replaceAll("_", " ")}: {count}</span>
                ))}
                {Object.keys(dashboard.student_analytics.applications_by_status).length === 0 && <p className="text-sm text-muted-foreground">No application status data yet.</p>}
              </div>
            </section>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <section className="lg:col-span-2 border border-border rounded-xl bg-card p-5">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-semibold">Applications</h2>
                  <Link href="/applications" className="text-sm text-primary hover:underline">View all</Link>
                </div>
                {dashboard.applications.length === 0 ? <Empty title="No applications yet" body="Apply to a job to start tracking your pipeline." /> : (
                  <div className="space-y-3">
                    {dashboard.applications.slice(0, 5).map((application) => (
                      <Link key={application.id} href="/applications" className="block border border-border rounded-lg p-3 hover:bg-muted">
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <p className="text-sm font-medium">{application.job_title}</p>
                            <p className="text-xs text-muted-foreground">{application.company_name}</p>
                          </div>
                          <span className="badge-primary">{application.stage_display}</span>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </section>

              <section className="border border-border rounded-xl bg-card p-5">
                <h2 className="font-semibold mb-4">Career goals</h2>
                <div className="space-y-3 text-sm">
                  <p><span className="text-muted-foreground">Target role:</span> {dashboard.career_goals.desired_role || "Not set"}</p>
                  <p><span className="text-muted-foreground">Remote preference:</span> {dashboard.career_goals.remote_preference || "Not set"}</p>
                  <p><span className="text-muted-foreground">Open to work:</span> {dashboard.career_goals.open_to_work ? "Yes" : "No"}</p>
                </div>
                <div className="flex flex-wrap gap-1.5 mt-4">
                  {dashboard.skills_summary.map((skill) => <span key={skill} className="tag">{skill}</span>)}
                </div>
              </section>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <section className="border border-border rounded-xl bg-card p-5">
                <h2 className="font-semibold mb-4">Recommended jobs</h2>
                {dashboard.recommended_jobs.length === 0 ? <p className="text-sm text-muted-foreground">No recommendations yet.</p> : dashboard.recommended_jobs.map((job) => (
                  <Link key={job.id} href={`/jobs/${job.id}`} onClick={() => void trackRecommendedJobClick(job.id)} className="block border-b border-border last:border-0 py-3">
                    <p className="text-sm font-medium">{job.title}</p>
                    <p className="text-xs text-muted-foreground">{job.company_name} - {job.salary_display}</p>
                    {job.recommendation_reasons?.[0] && <p className="text-xs text-primary mt-1">{job.recommendation_reasons[0]}</p>}
                  </Link>
                ))}
              </section>

              <section className="border border-border rounded-xl bg-card p-5">
                <h2 className="font-semibold mb-4">Saved jobs</h2>
                {dashboard.saved_jobs.length === 0 ? <p className="text-sm text-muted-foreground">Save jobs to compare them later.</p> : dashboard.saved_jobs.map((saved) => (
                  <Link key={saved.id} href={`/jobs/${saved.job.id}`} className="block border-b border-border last:border-0 py-3">
                    <p className="text-sm font-medium">{saved.job.title}</p>
                    <p className="text-xs text-muted-foreground">{saved.collection_name || "Saved"}</p>
                  </Link>
                ))}
              </section>

              <section className="border border-border rounded-xl bg-card p-5">
                <h2 className="font-semibold mb-4">AI and recruiter activity</h2>
                <p className="text-sm">AI tutor sessions: <span className="font-medium">{dashboard.ai_usage_summary.ai_tutor_used}</span></p>
                <p className="text-sm mt-2">Resume analysis: <span className="font-medium">Available soon</span></p>
                <p className="text-sm mt-2">Portfolio analysis: <span className="font-medium">Available soon</span></p>
                <div className="mt-4 border-t border-border pt-4">
                  {dashboard.recent_recruiter_activity.length === 0 ? <p className="text-sm text-muted-foreground">No recruiter activity yet.</p> : dashboard.recent_recruiter_activity.map((item) => (
                    <p key={item.id} className="text-xs text-muted-foreground mb-2">{item.name.replaceAll("_", " ")} - {new Date(item.occurred_at).toLocaleDateString()}</p>
                  ))}
                </div>
              </section>
            </div>
          </>
        )}
      </main>
    </>
  );
}
