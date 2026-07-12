import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";

const HELP_ITEMS = [
  ["Learners", "Find courses, follow career tracks, manage resumes, build portfolios, and apply to jobs."],
  ["Recruiters", "Post jobs, review applications, manage interviews, save candidates, and work inside your organization."],
  ["Organizations", "Manage teams, cohorts, analytics, imports, exports, roles, and organization branding."],
  ["Trust", "Use certificate verification, privacy settings, notifications, and verification workflows to keep accounts safe."],
];

export default function HelpCentrePage() {
  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-5xl px-4 py-12">
        <p className="text-sm font-medium text-primary">Support</p>
        <h1 className="mt-2 text-3xl font-bold">Help centre</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">
          Get oriented around T-Career learning, job search, recruiting, organization management, and trust tools.
        </p>
        <div className="mt-8 grid gap-4 md:grid-cols-2">
          {HELP_ITEMS.map(([title, body]) => (
            <section key={title} className="rounded-xl border border-border bg-card p-5">
              <h2 className="font-semibold">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{body}</p>
            </section>
          ))}
        </div>
        <div className="mt-8 rounded-xl border border-border bg-muted/30 p-5">
          <h2 className="font-semibold">Quick links</h2>
          <div className="mt-4 flex flex-wrap gap-2">
            <Link href="/courses" className="btn-sm btn-secondary">Browse courses</Link>
            <Link href="/jobs" className="btn-sm btn-secondary">Browse jobs</Link>
            <Link href="/verify" className="btn-sm btn-secondary">Verify certificate</Link>
            <Link href="/settings/privacy" className="btn-sm btn-secondary">Privacy settings</Link>
          </div>
        </div>
      </main>
    </>
  );
}
