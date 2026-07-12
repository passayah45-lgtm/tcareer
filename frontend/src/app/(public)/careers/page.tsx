import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";

const TEAMS = ["Product engineering", "Learning design", "Career success", "Employer partnerships", "Trust and safety"];

export default function CareersPage() {
  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-5xl px-4 py-12">
        <p className="text-sm font-medium text-primary">Company</p>
        <h1 className="mt-2 text-3xl font-bold">Careers</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">
          T-Career is preparing the foundation for a team across learning, career marketplace, AI, enterprise, and platform operations.
        </p>
        <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {TEAMS.map((team) => (
            <div key={team} className="rounded-xl border border-border bg-card p-4 text-sm font-medium">{team}</div>
          ))}
        </div>
        <section className="mt-8 rounded-xl border border-border bg-muted/30 p-5">
          <h2 className="font-semibold">Open roles</h2>
          <p className="mt-2 text-sm text-muted-foreground">Public hiring pages are coming later. For now, explore the product and partner surfaces.</p>
          <Link href="/jobs" className="btn-base btn-primary mt-4 inline-flex">View marketplace jobs</Link>
        </section>
      </main>
    </>
  );
}
