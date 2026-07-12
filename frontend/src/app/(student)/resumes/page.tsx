"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import {
  archiveCareerResume,
  duplicateCareerResume,
  getCareerResumes,
  setDefaultCareerResume,
} from "@/lib/api/careers.api";
import type { CareerResume } from "@/types/careers.types";

export default function ResumesPage() {
  const [resumes, setResumes] = useState<CareerResume[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setResumes(await getCareerResumes());
      setError("");
    } catch {
      setError("Unable to load resumes.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function run(resumeId: string, action: "default" | "duplicate" | "archive") {
    setBusyId(resumeId);
    try {
      if (action === "default") await setDefaultCareerResume(resumeId);
      if (action === "duplicate") await duplicateCareerResume(resumeId);
      if (action === "archive") await archiveCareerResume(resumeId);
      await load();
    } catch {
      setError("Resume action failed.");
    } finally {
      setBusyId("");
    }
  }

  const active = resumes.filter((resume) => !resume.is_archived);
  const archived = resumes.filter((resume) => resume.is_archived);

  return (
    <>
      <Navbar />
      <main className="max-w-6xl mx-auto px-4 py-8 space-y-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold">Resumes</h1>
            <p className="text-sm text-muted-foreground mt-1">Manage tailored resumes, versions, private files, AI reviews, ATS checks, and usage analytics.</p>
          </div>
          <Link href="/resumes/new" className="btn-base btn-primary">New resume</Link>
        </div>

        {error && <div className="border border-destructive/30 rounded-xl p-4 text-sm text-destructive">{error}</div>}
        {loading && <div className="h-64 rounded-xl bg-muted animate-pulse" />}
        {!loading && active.length === 0 && (
          <section className="border border-border rounded-xl bg-card p-8 text-center">
            <h2 className="text-lg font-semibold">No resumes yet</h2>
            <p className="text-sm text-muted-foreground mt-2">Create your first resume and use it when applying for jobs.</p>
            <Link href="/resumes/new" className="btn-base btn-primary mt-5 inline-flex">Create resume</Link>
          </section>
        )}

        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {active.map((resume) => (
            <article key={resume.id} className="border border-border rounded-xl bg-card p-5 space-y-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="font-semibold">{resume.title}</h2>
                  <p className="text-sm text-muted-foreground">{resume.target_role || "Target role not set"}</p>
                </div>
                {resume.is_default && <span className="badge-primary">Default</span>}
              </div>
              <p className="text-sm text-muted-foreground line-clamp-3">{resume.summary || "No summary yet."}</p>
              <div className="grid grid-cols-3 gap-2">
                <div className="stat-card"><span className="stat-value">{resume.versions.length}</span><span className="stat-label">Versions</span></div>
                <div className="stat-card"><span className="stat-value">{resume.files.length}</span><span className="stat-label">Files</span></div>
                <div className="stat-card"><span className="stat-value">{resume.analytics?.length ?? 0}</span><span className="stat-label">Events</span></div>
              </div>
              <div className="flex flex-wrap gap-2">
                <Link href={`/resumes/${resume.id}`} className="btn-base btn-secondary">Preview</Link>
                <Link href={`/resumes/${resume.id}/edit`} className="btn-base btn-secondary">Edit</Link>
                {!resume.is_default && (
                  <button disabled={busyId === resume.id} onClick={() => void run(resume.id, "default")} className="btn-base btn-secondary">Set default</button>
                )}
                <button disabled={busyId === resume.id} onClick={() => void run(resume.id, "duplicate")} className="btn-base btn-secondary">Duplicate</button>
                <button disabled={busyId === resume.id} onClick={() => void run(resume.id, "archive")} className="btn-base btn-secondary">Archive</button>
              </div>
            </article>
          ))}
        </section>

        {archived.length > 0 && (
          <section className="border border-border rounded-xl bg-card p-5">
            <h2 className="font-semibold mb-3">Archived</h2>
            <div className="space-y-2">
              {archived.map((resume) => (
                <p key={resume.id} className="text-sm text-muted-foreground">{resume.title}</p>
              ))}
            </div>
          </section>
        )}
      </main>
    </>
  );
}
