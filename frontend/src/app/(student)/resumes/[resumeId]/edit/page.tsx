"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { getCareerResume, updateCareerResume } from "@/lib/api/careers.api";

export default function EditResumePage() {
  const params = useParams<{ resumeId: string }>();
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [summary, setSummary] = useState("");
  const [skills, setSkills] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const resume = await getCareerResume(params.resumeId);
      setTitle(resume.title);
      setTargetRole(resume.target_role);
      setSummary(resume.summary);
      setSkills(resume.skills.join(", "));
      setError("");
    } catch {
      setError("Unable to load resume.");
    } finally {
      setLoading(false);
    }
  }, [params.resumeId]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
      await updateCareerResume(params.resumeId, {
        title,
        target_role: targetRole,
        summary,
        skills: skills.split(",").map((skill) => skill.trim()).filter(Boolean),
      });
      router.push(`/resumes/${params.resumeId}`);
    } catch {
      setError("Unable to update resume.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <Navbar />
      <main className="max-w-3xl mx-auto px-4 py-8">
        <h1 className="text-2xl md:text-3xl font-bold">Edit resume</h1>
        <p className="text-sm text-muted-foreground mt-1">Every save creates a version snapshot.</p>
        {loading && <div className="h-64 rounded-xl bg-muted animate-pulse mt-6" />}
        {error && <div className="border border-destructive/30 rounded-xl p-4 text-sm text-destructive mt-5">{error}</div>}
        {!loading && (
          <form onSubmit={submit} className="border border-border rounded-xl bg-card p-6 mt-6 space-y-4">
            <label className="block">
              <span className="text-sm font-medium">Title</span>
              <input className="input mt-1" value={title} onChange={(event) => setTitle(event.target.value)} required />
            </label>
            <label className="block">
              <span className="text-sm font-medium">Target role</span>
              <input className="input mt-1" value={targetRole} onChange={(event) => setTargetRole(event.target.value)} />
            </label>
            <label className="block">
              <span className="text-sm font-medium">Summary</span>
              <textarea className="input mt-1 min-h-36" value={summary} onChange={(event) => setSummary(event.target.value)} />
            </label>
            <label className="block">
              <span className="text-sm font-medium">Skills</span>
              <input className="input mt-1" value={skills} onChange={(event) => setSkills(event.target.value)} />
            </label>
            <button disabled={saving} className="btn-base btn-primary">{saving ? "Saving..." : "Save changes"}</button>
          </form>
        )}
      </main>
    </>
  );
}
