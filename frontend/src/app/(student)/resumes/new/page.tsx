"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { createCareerResume } from "@/lib/api/careers.api";

export default function NewResumePage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [summary, setSummary] = useState("");
  const [skills, setSkills] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
      const resume = await createCareerResume({
        title,
        target_role: targetRole,
        summary,
        skills: skills.split(",").map((skill) => skill.trim()).filter(Boolean),
      });
      router.push(`/resumes/${resume.id}`);
    } catch {
      setError("Unable to create resume.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <Navbar />
      <main className="max-w-3xl mx-auto px-4 py-8">
        <h1 className="text-2xl md:text-3xl font-bold">New resume</h1>
        <p className="text-sm text-muted-foreground mt-1">Start a resume tailored to a role or application.</p>
        {error && <div className="border border-destructive/30 rounded-xl p-4 text-sm text-destructive mt-5">{error}</div>}
        <form onSubmit={submit} className="border border-border rounded-xl bg-card p-6 mt-6 space-y-4">
          <label className="block">
            <span className="text-sm font-medium">Title</span>
            <input className="input mt-1" value={title} onChange={(event) => setTitle(event.target.value)} required placeholder="Data Analyst Resume" />
          </label>
          <label className="block">
            <span className="text-sm font-medium">Target role</span>
            <input className="input mt-1" value={targetRole} onChange={(event) => setTargetRole(event.target.value)} placeholder="Junior Data Analyst" />
          </label>
          <label className="block">
            <span className="text-sm font-medium">Summary</span>
            <textarea className="input mt-1 min-h-32" value={summary} onChange={(event) => setSummary(event.target.value)} placeholder="A concise career summary..." />
          </label>
          <label className="block">
            <span className="text-sm font-medium">Skills</span>
            <input className="input mt-1" value={skills} onChange={(event) => setSkills(event.target.value)} placeholder="Python, SQL, Excel" />
          </label>
          <button disabled={saving} className="btn-base btn-primary">{saving ? "Creating..." : "Create resume"}</button>
        </form>
      </main>
    </>
  );
}
