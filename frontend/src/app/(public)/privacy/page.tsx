import { Navbar } from "@/components/layout/Navbar";

const SECTIONS = [
  ["Account data", "T-Career stores account details needed for authentication, learning progress, certificates, career profiles, applications, and organization membership."],
  ["Career visibility", "Students control public profile, recruiter resume visibility, portfolio visibility, open-to-work status, and recruiter contact preferences."],
  ["Recruiter access", "Recruiters see candidate information only when candidate visibility, organization permissions, and entitlement checks allow it."],
  ["AI privacy", "AI features use the centralized AI service with privacy redaction, moderation, usage tracking, budgets, and feature flags."],
  ["Audit and security", "Privileged actions, privacy changes, candidate access, verification decisions, email operations, and admin activity are recorded for trust and compliance."],
];

export default function PrivacyPolicyPage() {
  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-4xl px-4 py-12">
        <p className="text-sm font-medium text-primary">Trust & support</p>
        <h1 className="mt-2 text-3xl font-bold">Privacy policy</h1>
        <p className="mt-3 text-sm leading-7 text-muted-foreground">
          This product preview policy summarizes the privacy principles currently represented in the T-Career platform.
        </p>
        <div className="mt-8 space-y-4">
          {SECTIONS.map(([title, body]) => (
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
