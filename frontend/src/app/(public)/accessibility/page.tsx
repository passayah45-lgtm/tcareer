import { Navbar } from "@/components/layout/Navbar";

const ACCESSIBILITY = [
  ["Readable interfaces", "T-Career aims for clear labels, predictable navigation, responsive layouts, and readable contrast across devices."],
  ["Keyboard access", "Core links, forms, controls, dashboards, and settings should remain usable without pointer-only interaction."],
  ["Inclusive learning", "Course, certificate, resume, portfolio, and career tools should support learners with different needs and device constraints."],
  ["Continuous improvement", "Accessibility review should be part of every production-readiness pass before broad launch."],
];

export default function AccessibilityPage() {
  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-5xl px-4 py-12">
        <p className="text-sm font-medium text-primary">Trust & support</p>
        <h1 className="mt-2 text-3xl font-bold">Accessibility</h1>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-muted-foreground">
          T-Career should be usable by learners, recruiters, instructors, and organization admins across devices and access needs.
        </p>
        <div className="mt-8 grid gap-4 md:grid-cols-2">
          {ACCESSIBILITY.map(([title, body]) => (
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
