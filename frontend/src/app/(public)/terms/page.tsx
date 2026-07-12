import { Navbar } from "@/components/layout/Navbar";

const TERMS = [
  ["Learning platform", "Learners use T-Career to access courses, tracks, AI learning support, certificates, resumes, portfolios, and career tools."],
  ["Career marketplace", "Job applications, recruiter views, candidate unlocks, interviews, and organization workflows must respect candidate privacy and platform permissions."],
  ["Organizations", "Companies, universities, and partners are responsible for inviting authorized users, assigning scoped roles, and using exports/imports appropriately."],
  ["Certificates", "Verified certificates can be checked publicly by certificate number. Revoked certificates should not be represented as active credentials."],
  ["Acceptable use", "Users must not misuse candidate data, impersonate organizations, submit fraudulent verification documents, or attempt to bypass platform controls."],
];

export default function TermsPage() {
  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-4xl px-4 py-12">
        <p className="text-sm font-medium text-primary">Trust & support</p>
        <h1 className="mt-2 text-3xl font-bold">Terms of service</h1>
        <p className="mt-3 text-sm leading-7 text-muted-foreground">
          These preview terms describe the expected use of T-Career while the platform is prepared for beta and production readiness.
        </p>
        <div className="mt-8 space-y-4">
          {TERMS.map(([title, body]) => (
            <section key={title} className="rounded-xl border border-border bg-card p-5">
              <h2 className="font-semibold">{title}</h2>
              <p className="mt-2 text-sm leading-7 text-muted-foreground">{body}</p>
            </section>
          ))}
        </div>
      </main>
    </>
  );
}
