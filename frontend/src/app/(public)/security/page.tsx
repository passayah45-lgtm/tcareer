import { Navbar } from "@/components/layout/Navbar";

const SECURITY = [
  ["Authentication", "Refresh tokens use HttpOnly cookie flow, CSRF-safe refresh/logout behavior, and scoped throttling foundations."],
  ["Authorization", "PermissionService and EntitlementService centralize role, organization, recruiter, candidate, and access decisions."],
  ["Auditability", "Privileged actions, verification decisions, privacy changes, candidate access, email operations, and admin actions are logged."],
  ["Private files", "Resume, portfolio, and verification file access is designed around validation, authorization, and private download helpers."],
];

export default function SecurityPage() {
  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-5xl px-4 py-12">
        <p className="text-sm font-medium text-primary">Trust & support</p>
        <h1 className="mt-2 text-3xl font-bold">Security</h1>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-muted-foreground">
          T-Career is being built with explicit security, privacy, audit, and operational readiness foundations before production launch.
        </p>
        <div className="mt-8 grid gap-4 md:grid-cols-2">
          {SECURITY.map(([title, body]) => (
            <section key={title} className="rounded-xl border border-border bg-card p-5">
              <h2 className="font-semibold">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{body}</p>
            </section>
          ))}
        </div>
      </main>
    </>
  );
}
