"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import {
  downloadCareerResume,
  getResumeAIAnalytics,
  getResumeAIHistory,
  getCareerResume,
  runResumeAIATS,
  runResumeAIComparison,
  runResumeAIJobMatch,
  runResumeAIReview,
  runResumeAISkillExtraction,
  setDefaultCareerResume,
  uploadCareerResumeBinary,
  uploadCareerResumeFile,
} from "@/lib/api/careers.api";
import type { CareerResume, ResumeAIAnalytics, ResumeAIReview } from "@/types/careers.types";

export default function ResumeDetailPage() {
  const params = useParams<{ resumeId: string }>();
  const [resume, setResume] = useState<CareerResume | null>(null);
  const [fileUrl, setFileUrl] = useState("");
  const [fileName, setFileName] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [aiHistory, setAiHistory] = useState<ResumeAIReview[]>([]);
  const [aiAnalytics, setAiAnalytics] = useState<ResumeAIAnalytics | null>(null);
  const [jobId, setJobId] = useState("");
  const [comparisonResumeId, setComparisonResumeId] = useState("");
  const [aiBusy, setAiBusy] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [nextResume, nextHistory, nextAnalytics] = await Promise.all([
        getCareerResume(params.resumeId),
        getResumeAIHistory(params.resumeId),
        getResumeAIAnalytics(params.resumeId),
      ]);
      setResume(nextResume);
      setAiHistory(nextHistory);
      setAiAnalytics(nextAnalytics);
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

  async function upload() {
    if (!selectedFile && (!fileUrl || !fileName)) return;
    try {
      if (selectedFile) {
        await uploadCareerResumeBinary(params.resumeId, selectedFile);
      } else {
        await uploadCareerResumeFile(params.resumeId, { file_url: fileUrl, file_name: fileName, is_private: true });
      }
      setFileUrl("");
      setFileName("");
      setSelectedFile(null);
      setMessage("Private resume file added.");
      await load();
    } catch {
      setError("Unable to add resume file.");
    }
  }

  async function download() {
    try {
      const result = await downloadCareerResume(params.resumeId);
      setMessage(`Download tracked: ${result.file_name || "structured resume"}`);
      if (result.download_url) window.open(result.download_url, "_blank", "noopener,noreferrer");
      await load();
    } catch {
      setError("Unable to download resume.");
    }
  }

  async function runAI(action: "review" | "skills" | "ats" | "match" | "compare") {
    setAiBusy(action);
    setError("");
    try {
      if (action === "review") await runResumeAIReview(params.resumeId);
      if (action === "skills") await runResumeAISkillExtraction(params.resumeId);
      if (action === "ats") await runResumeAIATS(params.resumeId);
      if (action === "match") {
        if (!jobId) {
          setError("Add a job ID before running match.");
          return;
        }
        await runResumeAIJobMatch(params.resumeId, jobId);
      }
      if (action === "compare") {
        if (!comparisonResumeId) {
          setError("Add another resume ID before comparing.");
          return;
        }
        await runResumeAIComparison(params.resumeId, comparisonResumeId);
      }
      setMessage("AI analysis completed.");
      await load();
    } catch {
      setError("AI resume analysis failed.");
    } finally {
      setAiBusy("");
    }
  }

  const latestReview = aiHistory[0];
  const resumeAnalytics = resume?.analytics ?? [];

  return (
    <>
      <Navbar />
      <main className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        {loading && <div className="h-72 rounded-xl bg-muted animate-pulse" />}
        {error && <div className="border border-destructive/30 rounded-xl p-4 text-sm text-destructive">{error}</div>}
        {message && <div className="border border-primary/30 rounded-xl p-4 text-sm text-primary">{message}</div>}
        {resume && (
          <>
            <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl md:text-3xl font-bold">{resume.title}</h1>
                  {resume.is_default && <span className="badge-primary">Default</span>}
                </div>
                <p className="text-sm text-muted-foreground mt-1">{resume.target_role || "Target role not set"}</p>
              </div>
              <div className="flex gap-2">
                <Link href={`/resumes/${resume.id}/edit`} className="btn-base btn-secondary">Edit</Link>
                {!resume.is_default && <button onClick={() => void setDefaultCareerResume(resume.id).then(load)} className="btn-base btn-secondary">Set default</button>}
                <button onClick={() => void download()} className="btn-base btn-primary">Download</button>
              </div>
            </div>

            <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <article className="lg:col-span-2 border border-border rounded-xl bg-card p-6 space-y-5">
                <div>
                  <h2 className="font-semibold">Summary</h2>
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap mt-2">{resume.summary || "No summary yet."}</p>
                </div>
                <div>
                  <h2 className="font-semibold">Skills</h2>
                  <div className="flex flex-wrap gap-1.5 mt-2">{resume.skills.map((skill) => <span key={skill} className="tag">{skill}</span>)}</div>
                </div>
                <div>
                  <h2 className="font-semibold">Experience</h2>
                  {resume.experience.length === 0 ? <p className="text-sm text-muted-foreground mt-2">No experience entries yet.</p> : resume.experience.map((item) => (
                    <p key={item.id} className="text-sm mt-2">{item.title} at {item.company}</p>
                  ))}
                </div>
                <div>
                  <h2 className="font-semibold">Education</h2>
                  {resume.education.length === 0 ? <p className="text-sm text-muted-foreground mt-2">No education entries yet.</p> : resume.education.map((item) => (
                    <p key={item.id} className="text-sm mt-2">{item.degree} - {item.institution}</p>
                  ))}
                </div>
              </article>

              <aside className="space-y-6">
                <section className="border border-border rounded-xl bg-card p-5">
                  <h2 className="font-semibold">AI Resume Intelligence</h2>
                  <p className="text-sm text-muted-foreground mt-1">Generate structured feedback, ATS checks, skill extraction, and job fit analysis.</p>
                  {latestReview && (
                    <div className="grid grid-cols-3 gap-2 mt-4">
                      <div className="stat-card"><span className="stat-value">{latestReview.overall_score}</span><span className="stat-label">Score</span></div>
                      <div className="stat-card"><span className="stat-value">{latestReview.ats_score}</span><span className="stat-label">ATS</span></div>
                      <div className="stat-card"><span className="stat-value">{latestReview.confidence}</span><span className="stat-label">Confidence</span></div>
                    </div>
                  )}
                  <div className="flex flex-wrap gap-2 mt-4">
                    <button disabled={Boolean(aiBusy)} onClick={() => void runAI("review")} className="btn-base btn-primary">{aiBusy === "review" ? "Reviewing..." : "Review"}</button>
                    <button disabled={Boolean(aiBusy)} onClick={() => void runAI("ats")} className="btn-base btn-secondary">ATS</button>
                    <button disabled={Boolean(aiBusy)} onClick={() => void runAI("skills")} className="btn-base btn-secondary">Extract skills</button>
                  </div>
                  <input className="input mt-4" value={jobId} onChange={(event) => setJobId(event.target.value)} placeholder="Job ID for match" />
                  <button disabled={Boolean(aiBusy)} onClick={() => void runAI("match")} className="btn-base btn-secondary mt-2 w-full">Run job match</button>
                  <input className="input mt-4" value={comparisonResumeId} onChange={(event) => setComparisonResumeId(event.target.value)} placeholder="Resume ID to compare" />
                  <button disabled={Boolean(aiBusy)} onClick={() => void runAI("compare")} className="btn-base btn-secondary mt-2 w-full">Compare resumes</button>
                  {latestReview && (
                    <div className="mt-4 space-y-3">
                      <p className="text-sm text-muted-foreground">{latestReview.summary}</p>
                      <div>
                        <h3 className="text-sm font-medium">Top actions</h3>
                        <ul className="mt-2 space-y-1">
                          {latestReview.action_items.slice(0, 3).map((item) => (
                            <li key={item.action} className="text-sm text-muted-foreground">{item.priority}: {item.action}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}
                </section>
                <section className="border border-border rounded-xl bg-card p-5">
                  <h2 className="font-semibold mb-3">Private files</h2>
                  <div className="space-y-2">
                    {resume.files.length === 0 && <p className="text-sm text-muted-foreground">No private files uploaded yet.</p>}
                    {resume.files.map((file) => <p key={file.id} className="text-sm">{file.file_name} {file.is_private ? "(private)" : ""} {file.file_size ? `- ${Math.round(file.file_size / 1024)} KB` : ""}</p>)}
                  </div>
                  <label className="block mt-4">
                    <span className="text-xs text-muted-foreground">Upload PDF, DOC, or DOCX</span>
                    <input className="input mt-1" type="file" accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={(event) => setSelectedFile(event.target.files?.[0] || null)} />
                  </label>
                  <div className="text-xs text-muted-foreground mt-4">Compatible URL fallback</div>
                  <input className="input mt-4" value={fileName} onChange={(event) => setFileName(event.target.value)} placeholder="File name" />
                  <input className="input mt-2" value={fileUrl} onChange={(event) => setFileUrl(event.target.value)} placeholder="Private file URL" />
                  <button type="button" onClick={() => void upload()} className="btn-base btn-secondary mt-3 w-full">Upload private file</button>
                </section>
                <section className="border border-border rounded-xl bg-card p-5">
                  <h2 className="font-semibold mb-3">Usage analytics</h2>
                  <p className="text-sm text-muted-foreground">Downloads: {resumeAnalytics.filter((item) => item.event_type === "downloaded").length}</p>
                  <p className="text-sm text-muted-foreground mt-2">Applications: {resumeAnalytics.filter((item) => item.event_type === "used_for_application").length}</p>
                  <p className="text-sm text-muted-foreground mt-2">Recruiter views: {resumeAnalytics.filter((item) => item.event_type === "viewed_by_recruiter").length}</p>
                  <p className="text-sm text-muted-foreground mt-2">AI reviews: {aiAnalytics?.review_count ?? 0}</p>
                  <p className="text-sm text-muted-foreground mt-2">Best AI score: {aiAnalytics?.best_score ?? 0}</p>
                </section>
                <section className="border border-border rounded-xl bg-card p-5">
                  <h2 className="font-semibold mb-3">AI history</h2>
                  {aiHistory.length === 0 && <p className="text-sm text-muted-foreground">No AI reviews yet.</p>}
                  {aiHistory.slice(0, 5).map((review) => (
                    <div key={review.id} className="border-t border-border py-2 first:border-t-0 first:pt-0">
                      <p className="text-sm font-medium">{review.review_type.replace("_", " ")} - {review.overall_score}/100</p>
                      <p className="text-xs text-muted-foreground">{new Date(review.created_at).toLocaleString()}</p>
                    </div>
                  ))}
                </section>
                <section className="border border-border rounded-xl bg-card p-5">
                  <h2 className="font-semibold mb-3">Version history</h2>
                  {resume.versions.map((version) => (
                    <p key={version.id} className="text-sm">v{version.version_number}: {version.change_summary || "Snapshot saved"}</p>
                  ))}
                </section>
              </aside>
            </section>
          </>
        )}
      </main>
    </>
  );
}
