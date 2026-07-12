import { Navbar } from "@/components/layout/Navbar";

const VALUES = [
  ["Learning to opportunity", "T-Career connects courses, certificates, resumes, portfolios, jobs, and recruiter workflows in one path."],
  ["Trust by design", "Verification, audit logs, privacy controls, and candidate visibility rules are part of the product foundation."],
  ["AI with guardrails", "AI features route through centralized services for moderation, privacy redaction, budgets, and provider abstraction."],
];

export default function AboutPage() {
  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-5xl px-4 py-12">
        <p className="text-sm font-medium text-primary">Company</p>
        <h1 className="mt-2 text-3xl font-bold">About T-Career</h1>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-muted-foreground">
          T-Career is a learning and career marketplace built to help students gain practical skills, prove progress, and connect with employers through trusted career profiles.
        </p>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {VALUES.map(([title, body]) => (
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
