"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { applyToJob, browseJobs, getJob, previewApplication, saveApplicationDraft, saveJob } from "@/lib/api/student-career.api";
import { getCareerResumes, getMyPortfolio } from "@/lib/api/careers.api";
import { useAuthStore } from "@/stores/auth.store";
import type { ApplicationPreview, StudentApplication, StudentJob } from "@/types/student-career.types";
import type { CareerResume, Portfolio } from "@/types/careers.types";

export default function JobDetailPage() {
  const params = useParams<{ jobId: string }>();
  const { isAuthenticated } = useAuthStore();
  const [job, setJob] = useState<StudentJob | null>(null);
  const [related, setRelated] = useState<StudentJob[]>([]);
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [resumes, setResumes] = useState<CareerResume[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState("");
  const [application, setApplication] = useState<StudentApplication | null>(null);
  const [preview, setPreview] = useState<ApplicationPreview | null>(null);
  const [coverLetter, setCoverLetter] = useState("");
  const [answers, setAnswers] = useState<Record<string, string | number | boolean>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const jobData = await getJob(params.jobId);
      setJob(jobData);
      const relatedData = await browseJobs({ skills: jobData.required_skills.slice(0, 2).join(","), page_size: 3 });
      setRelated(relatedData.results.filter((item) => item.id !== jobData.id).slice(0, 3));
      if (isAuthenticated) {
        await Promise.all([
          getMyPortfolio().then(setPortfolio).catch(() => undefined),
          getCareerResumes().then((items) => {
            const active = items.filter((item) => !item.is_archived);
            setResumes(active);
            setSelectedResumeId(active.find((item) => item.is_default)?.id || active[0]?.id || "");
          }).catch(() => undefined),
        ]);
      }
      setError("");
    } catch {
      setError("Unable to load job detail.");
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, params.jobId]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function submit(event: FormEvent, mode: "draft" | "apply") {
    event.preventDefault();
    if (!job || !isAuthenticated) return;
    setSaving(mode);
    try {
      const payload = {
        cover_letter: coverLetter,
        resume_id: selectedResumeId || undefined,
        portfolio_id: portfolio?.id,
        answers: answerPayload(),
      };
      const result = mode === "draft" ? await saveApplicationDraft(job.id, payload) : await applyToJob(job.id, payload);
      setApplication(result);
      setError("");
    } catch {
      setError("Application action failed. Check sign-in and try again.");
    } finally {
      setSaving("");
    }
  }

  function answerPayload() {
    return Object.entries(answers).map(([question, value]) => ({ question, answer: { value } }));
  }

  async function previewCurrentApplication() {
    if (!job || !isAuthenticated) return;
    setSaving("preview");
    try {
      setPreview(await previewApplication(job.id, {
        cover_letter: coverLetter,
        resume_id: selectedResumeId || undefined,
        portfolio_id: portfolio?.id,
        answers: answerPayload(),
      }));
      setError("");
    } catch {
      setError("Unable to preview this application.");
    } finally {
      setSaving("");
    }
  }

  async function saveCurrentJob() {
    if (!job) return;
    await saveJob({ job_id: job.id });
  }

  return (
    <>
      <Navbar />
      <main className="max-w-6xl mx-auto px-4 py-8">
        {loading && <div className="h-72 bg-muted rounded-xl animate-pulse" />}
        {error && <div className="border border-destructive/30 rounded-xl p-5 text-sm text-destructive mb-5">{error}</div>}
        {job && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <section className="lg:col-span-2 space-y-6">
              <div className="border border-border rounded-xl bg-card p-6">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">{job.company_name} {job.organization_name ? `- ${job.organization_name}` : ""}</p>
                    <h1 className="text-2xl md:text-3xl font-bold mt-1">{job.title}</h1>
                    <p className="text-sm text-muted-foreground mt-2">{job.location} - {job.job_type_display} - {job.experience_level_display}</p>
                  </div>
                  {job.organization_name && <span className="badge-success">Verified</span>}
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6">
                  <div className="stat-card"><span className="stat-value">{job.salary_display}</span><span className="stat-label">Salary</span></div>
                  <div className="stat-card"><span className="stat-value">{job.is_remote ? "Remote" : "Onsite"}</span><span className="stat-label">Work mode</span></div>
                  <div className="stat-card"><span className="stat-value">{job.views_count}</span><span className="stat-label">Views</span></div>
                  <div className="stat-card"><span className="stat-value">{job.expires_at ? new Date(job.expires_at).toLocaleDateString() : "Open"}</span><span className="stat-label">Deadline</span></div>
                </div>
              </div>

              <div className="border border-border rounded-xl bg-card p-6">
                <h2 className="font-semibold mb-3">Description and responsibilities</h2>
                <p className="text-sm whitespace-pre-wrap text-muted-foreground">{job.description}</p>
              </div>

              <div className="border border-border rounded-xl bg-card p-6">
                <h2 className="font-semibold mb-3">Requirements and skills</h2>
                <ul className="list-disc pl-5 text-sm text-muted-foreground space-y-1">
                  {job.requirements.map((item) => <li key={item}>{item}</li>)}
                </ul>
                <div className="flex flex-wrap gap-1.5 mt-4">
                  {[...job.required_skills, ...job.preferred_skills].map((skill) => <span key={skill} className="tag">{skill}</span>)}
                </div>
              </div>
            </section>

            <aside className="space-y-6">
              <section className="border border-border rounded-xl bg-card p-5">
                <h2 className="font-semibold mb-4">Apply</h2>
                {!isAuthenticated ? (
                  <Link href={`/login?next=/jobs/${job.id}`} className="btn-base btn-primary w-full">Sign in to apply</Link>
                ) : (
                  <form className="space-y-3">
                    {resumes.length > 0 ? (
                      <label className="block">
                        <span className="text-xs text-muted-foreground">Resume</span>
                        <select className="input mt-1" value={selectedResumeId} onChange={(event) => setSelectedResumeId(event.target.value)}>
                          {resumes.map((item) => (
                            <option key={item.id} value={item.id}>{item.title}{item.is_default ? " (default)" : ""}</option>
                          ))}
                        </select>
                      </label>
                    ) : (
                      <Link href="/resumes/new" className="text-sm text-primary">Create a resume before applying</Link>
                    )}
                    <p className="text-xs text-muted-foreground">Portfolio: {portfolio?.headline || "No portfolio headline yet"}</p>
                    <textarea className="input min-h-32" value={coverLetter} onChange={(e) => setCoverLetter(e.target.value)} placeholder="Write a focused cover letter..." />
                    {job.application_questions.length > 0 && (
                      <div className="space-y-3">
                        <p className="text-sm font-medium">Application questions</p>
                        {job.application_questions.map((question) => (
                          <label key={question.id} className="block">
                            <span className="text-xs text-muted-foreground">{question.question_text}{question.is_required ? " *" : ""}</span>
                            {question.question_type === "long_text" && (
                              <textarea className="input mt-1 min-h-20" value={String(answers[question.id] ?? "")} onChange={(event) => setAnswers((prev) => ({ ...prev, [question.id]: event.target.value }))} />
                            )}
                            {question.question_type === "yes_no" && (
                              <select className="input mt-1" value={String(answers[question.id] ?? "")} onChange={(event) => setAnswers((prev) => ({ ...prev, [question.id]: event.target.value === "true" }))}>
                                <option value="">Choose</option>
                                <option value="true">Yes</option>
                                <option value="false">No</option>
                              </select>
                            )}
                            {question.question_type === "multiple_choice" && (
                              <select className="input mt-1" value={String(answers[question.id] ?? "")} onChange={(event) => setAnswers((prev) => ({ ...prev, [question.id]: event.target.value }))}>
                                <option value="">Choose</option>
                                {question.choices.map((choice) => <option key={choice} value={choice}>{choice}</option>)}
                              </select>
                            )}
                            {question.question_type === "number" && (
                              <input className="input mt-1" type="number" value={String(answers[question.id] ?? "")} onChange={(event) => setAnswers((prev) => ({ ...prev, [question.id]: Number(event.target.value) }))} />
                            )}
                            {["short_text", "url"].includes(question.question_type) && (
                              <input className="input mt-1" type={question.question_type === "url" ? "url" : "text"} value={String(answers[question.id] ?? "")} onChange={(event) => setAnswers((prev) => ({ ...prev, [question.id]: event.target.value }))} />
                            )}
                          </label>
                        ))}
                      </div>
                    )}
                    {application && <p className="text-sm text-primary">Application status: {application.stage_display}</p>}
                    {preview && (
                      <div className="border border-border rounded-lg p-3 text-xs space-y-2">
                        <p className="font-medium text-sm">Application preview</p>
                        <p>Job: {preview.job.title}</p>
                        <p>Resume: {preview.selected_resume?.title || "None selected"}</p>
                        <p>Portfolio: {preview.portfolio?.headline || "Not included"}</p>
                        <p>Cover letter: {preview.cover_letter ? `${preview.cover_letter.slice(0, 90)}${preview.cover_letter.length > 90 ? "..." : ""}` : "Empty"}</p>
                        {preview.answers.map((item) => <p key={item.question}>{item.question_text}: {String(item.answer.value)}</p>)}
                      </div>
                    )}
                    <div className="grid grid-cols-3 gap-2">
                      <button type="button" onClick={() => void previewCurrentApplication()} disabled={saving !== ""} className="btn-base btn-secondary">Preview</button>
                      <button onClick={(event) => submit(event, "draft")} disabled={saving !== ""} className="btn-base btn-secondary">Save draft</button>
                      <button onClick={(event) => submit(event, "apply")} disabled={saving !== ""} className="btn-base btn-primary">Apply</button>
                    </div>
                    <button type="button" onClick={saveCurrentJob} className="btn-base btn-secondary w-full">Save job</button>
                  </form>
                )}
              </section>

              <section className="border border-border rounded-xl bg-card p-5">
                <h2 className="font-semibold mb-4">Recruiter and company</h2>
                <p className="text-sm">{job.posted_by_name || "Recruiting team"}</p>
                <p className="text-xs text-muted-foreground mt-1">{job.company_name}</p>
                <p className="text-xs text-muted-foreground mt-1 capitalize">{job.organization_type?.replaceAll("_", " ") || "Company"}</p>
              </section>

              <section className="border border-border rounded-xl bg-card p-5">
                <h2 className="font-semibold mb-4">Related jobs</h2>
                {related.length === 0 ? <p className="text-sm text-muted-foreground">No related jobs yet.</p> : related.map((item) => (
                  <Link key={item.id} href={`/jobs/${item.id}`} className="block border-b border-border last:border-0 py-3">
                    <p className="text-sm font-medium">{item.title}</p>
                    <p className="text-xs text-muted-foreground">{item.company_name}</p>
                  </Link>
                ))}
              </section>
            </aside>
          </div>
        )}
      </main>
    </>
  );
}
