import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";

const CONTACTS = [
  ["Learner support", "Help with courses, certificates, resumes, portfolios, applications, and account settings."],
  ["Recruiter support", "Help with organization jobs, candidate search, applications, interviews, and recruiter seats."],
  ["University and company partnerships", "Discuss organization consoles, cohorts, teams, analytics, imports, exports, and reporting."],
];

export default function ContactPage() {
  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-5xl px-4 py-12">
        <p className="text-sm font-medium text-primary">Company</p>
        <h1 className="mt-2 text-3xl font-bold">Contact</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">
          Choose the right path for support, partnerships, recruiting, or organization workflows.
        </p>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {CONTACTS.map(([title, body]) => (
            <section key={title} className="rounded-xl border border-border bg-card p-5">
              <h2 className="font-semibold">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{body}</p>
            </section>
          ))}
        </div>
        <div className="mt-8 flex flex-wrap gap-2">
          <Link href="/help" className="btn-base btn-secondary">Help centre</Link>
          <Link href="/recruit" className="btn-base btn-primary">Recruiter interest</Link>
        </div>
      </main>
    </>
  );
}
