import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";

const POSTS = [
  ["How to build a career-ready portfolio", "Showcase projects, evidence, and outcomes that help recruiters understand your work."],
  ["Why verified certificates matter", "Make learning achievements easier for employers and universities to trust."],
  ["Using AI responsibly in career growth", "Use AI feedback for practice and improvement while keeping your voice and privacy intact."],
];

export default function BlogPage() {
  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-5xl px-4 py-12">
        <p className="text-sm font-medium text-primary">Company</p>
        <h1 className="mt-2 text-3xl font-bold">Blog</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">
          Notes on learning, career development, hiring, AI, verification, and the future of skills-based opportunity.
        </p>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {POSTS.map(([title, body]) => (
            <article key={title} className="rounded-xl border border-border bg-card p-5">
              <h2 className="font-semibold">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{body}</p>
              <Link href="/blog" className="mt-4 inline-block text-sm font-medium text-primary">Coming soon</Link>
            </article>
          ))}
        </div>
      </main>
    </>
  );
}
