"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import {
  addProjectMedia,
  createProject,
  getPortfolioAIAnalytics,
  getPortfolioAIHistory,
  getCareerResumes,
  getMyPortfolio,
  getMyResume,
  runPortfolioAIGitHubReview,
  runPortfolioAIJobMatch,
  runPortfolioAIProjectReview,
  runPortfolioAIReview,
  runPortfolioAISkillExtraction,
  updateMyPortfolio,
  updateProject,
  uploadProjectMedia,
} from "@/lib/api/careers.api";
import type { Portfolio, PortfolioAIAnalytics, PortfolioAIReview, Resume } from "@/types/careers.types";

export default function CareerProfilePage() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [resume, setResume] = useState<Resume | null>(null);
  const [resumeCount, setResumeCount] = useState(0);
  const [projectTitle, setProjectTitle] = useState("");
  const [projectTech, setProjectTech] = useState("");
  const [mediaProjectId, setMediaProjectId] = useState("");
  const [mediaUrl, setMediaUrl] = useState("");
  const [mediaFile, setMediaFile] = useState<File | null>(null);
  const [aiHistory, setAiHistory] = useState<PortfolioAIReview[]>([]);
  const [aiAnalytics, setAiAnalytics] = useState<PortfolioAIAnalytics | null>(null);
  const [aiProjectId, setAiProjectId] = useState("");
  const [aiJobId, setAiJobId] = useState("");
  const [aiBusy, setAiBusy] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [portfolioData, resumeData, resumes, history, analytics] = await Promise.all([
        getMyPortfolio(),
        getMyResume(),
        getCareerResumes().catch(() => []),
        getPortfolioAIHistory().catch(() => []),
        getPortfolioAIAnalytics().catch(() => null),
      ]);
      setPortfolio(portfolioData);
      setResume(resumeData);
      setResumeCount(resumes.length);
      setAiHistory(history);
      setAiAnalytics(analytics);
      setError("");
    } catch {
      setError("Unable to load career profile.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function changeVisibility(visibility: Portfolio["visibility"]) {
    const updated = await updateMyPortfolio({ visibility });
    setPortfolio(updated);
    setMessage("Portfolio visibility updated.");
  }

  async function addProject() {
    if (!projectTitle) return;
    await createProject({
      title: projectTitle,
      tech_stack: projectTech.split(",").map((item) => item.trim()).filter(Boolean),
      description: "",
    });
    setProjectTitle("");
    setProjectTech("");
    setMessage("Project added.");
    await load();
  }

  async function toggleFeatured(projectId: string, isFeatured: boolean) {
    await updateProject(projectId, { is_featured: !isFeatured });
    setMessage("Featured projects updated.");
    await load();
  }

  async function addMedia() {
    if (!mediaProjectId || (!mediaUrl && !mediaFile)) return;
    if (mediaFile) {
      await uploadProjectMedia(mediaProjectId, { file: mediaFile, visibility: "public", title: mediaFile.name });
    } else {
      await addProjectMedia(mediaProjectId, {
        media_type: mediaUrl.match(/\.(mp4|mov|webm)$/i) ? "video" : "image",
        url: mediaUrl,
        title: "Project media",
        visibility: "public",
      });
    }
    setMediaUrl("");
    setMediaFile(null);
    setMessage("Project media added.");
    await load();
  }

  async function runAI(action: "portfolio" | "project" | "github" | "skills" | "match") {
    setAiBusy(action);
    setError("");
    try {
      if (action === "portfolio") await runPortfolioAIReview();
      if (action === "project") {
        if (!aiProjectId) {
          setError("Choose a project before running project review.");
          return;
        }
        await runPortfolioAIProjectReview(aiProjectId);
      }
      if (action === "github") await runPortfolioAIGitHubReview(aiProjectId || undefined);
      if (action === "skills") await runPortfolioAISkillExtraction();
      if (action === "match") {
        if (!aiJobId) {
          setError("Add a job ID before running portfolio match.");
          return;
        }
        await runPortfolioAIJobMatch(aiJobId);
      }
      setMessage("Portfolio AI analysis completed.");
      await load();
    } catch {
      setError("Portfolio AI analysis failed.");
    } finally {
      setAiBusy("");
    }
  }

  const latestAI = aiHistory[0];

  return (
    <>
      <Navbar />
      <main className="max-w-6xl mx-auto px-4 py-8 space-y-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold">Career profile</h1>
            <p className="text-sm text-muted-foreground mt-1">Your public job-seeker identity: profile, resume, portfolio, privacy, and recruiter readiness.</p>
          </div>
          <div className="flex gap-2">
            <Link href="/portfolio/edit" className="btn-base btn-secondary">Edit portfolio</Link>
            <Link href="/resume/edit" className="btn-base btn-primary">Edit resume</Link>
          </div>
        </div>

        {loading && <div className="h-72 bg-muted rounded-xl animate-pulse" />}
        {error && <div className="border border-destructive/30 rounded-xl p-4 text-sm text-destructive">{error}</div>}
        {message && <div className="border border-primary/30 rounded-xl p-4 text-sm text-primary">{message}</div>}
        {portfolio && resume && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <section className="lg:col-span-2 border border-border rounded-xl bg-card p-6">
              <div className="flex items-start gap-4">
                <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center text-xl font-semibold">{portfolio.full_name?.[0] || "?"}</div>
                <div>
                  <h2 className="text-xl font-bold">{portfolio.full_name}</h2>
                  <p className="text-sm text-muted-foreground">{portfolio.headline || "Add a headline"}</p>
                  <p className="text-sm text-muted-foreground">{portfolio.location || "Location not set"}</p>
                </div>
                <span className="badge-primary ml-auto capitalize">{portfolio.visibility}</span>
              </div>
              <p className="text-sm mt-5 whitespace-pre-wrap">{portfolio.bio || "Add an about section so recruiters understand your story."}</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6">
                <div className="stat-card"><span className="stat-value">{portfolio.skills.length}</span><span className="stat-label">Skills</span></div>
                <div className="stat-card"><span className="stat-value">{portfolio.projects.length}</span><span className="stat-label">Projects</span></div>
                <div className="stat-card"><span className="stat-value">{resume.certificates.length}</span><span className="stat-label">Certificates</span></div>
                <div className="stat-card"><span className="stat-value">{portfolio.profile_views}</span><span className="stat-label">Portfolio views</span></div>
              </div>
            </section>

            <aside className="space-y-6">
              <section className="border border-border rounded-xl bg-card p-5">
                <h2 className="font-semibold mb-4">Availability and preferences</h2>
                <p className="text-sm">Desired role: {portfolio.desired_role || resume.target_role || "Not set"}</p>
                <p className="text-sm mt-2">Experience: {portfolio.experience_level}</p>
                <p className="text-sm mt-2">Privacy: {portfolio.visibility}</p>
                <p className="text-sm mt-2">Open to work: {portfolio.visibility === "public" ? "Visible" : "Limited"}</p>
                <select className="input mt-4" value={portfolio.visibility} onChange={(event) => void changeVisibility(event.target.value as Portfolio["visibility"])}>
                  <option value="public">Public</option>
                  <option value="unlisted">Unlisted</option>
                  <option value="private">Private</option>
                </select>
                {portfolio.public_url && <Link href={portfolio.public_url} className="btn-base btn-secondary mt-3 w-full">Public preview</Link>}
              </section>
              <section className="border border-border rounded-xl bg-card p-5">
                <h2 className="font-semibold mb-4">Portfolio analytics</h2>
                <p className="text-sm text-muted-foreground">Views: {portfolio.profile_views}</p>
                <p className="text-sm text-muted-foreground mt-2">Projects: {portfolio.projects.length}</p>
                <p className="text-sm text-muted-foreground mt-2">Resumes: {resumeCount}</p>
                <p className="text-sm text-muted-foreground mt-2">AI reviews: {aiAnalytics?.review_count ?? 0}</p>
                <p className="text-sm text-muted-foreground mt-2">Best AI score: {aiAnalytics?.best_score ?? 0}</p>
              </section>
            </aside>

            <section className="lg:col-span-3 border border-border rounded-xl bg-card p-5">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <h2 className="font-semibold">AI Portfolio Intelligence</h2>
                  <p className="text-sm text-muted-foreground mt-1">Review portfolio quality, individual projects, GitHub readiness, skills, and job fit.</p>
                </div>
                {latestAI && (
                  <div className="grid grid-cols-3 gap-2 min-w-[260px]">
                    <div className="stat-card"><span className="stat-value">{latestAI.overall_score}</span><span className="stat-label">Score</span></div>
                    <div className="stat-card"><span className="stat-value">{latestAI.project_score}</span><span className="stat-label">Projects</span></div>
                    <div className="stat-card"><span className="stat-value">{latestAI.confidence}</span><span className="stat-label">Confidence</span></div>
                  </div>
                )}
              </div>
              <div className="flex flex-wrap gap-2 mt-4">
                <button disabled={Boolean(aiBusy)} onClick={() => void runAI("portfolio")} className="btn-base btn-primary">{aiBusy === "portfolio" ? "Reviewing..." : "AI Review"}</button>
                <button disabled={Boolean(aiBusy)} onClick={() => void runAI("github")} className="btn-base btn-secondary">GitHub analysis</button>
                <button disabled={Boolean(aiBusy)} onClick={() => void runAI("skills")} className="btn-base btn-secondary">Extract skills</button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
                <div>
                  <select className="input" value={aiProjectId} onChange={(event) => setAiProjectId(event.target.value)}>
                    <option value="">Choose project for AI review</option>
                    {portfolio.projects.map((project) => <option key={project.id} value={project.id}>{project.title}</option>)}
                  </select>
                  <button disabled={Boolean(aiBusy)} onClick={() => void runAI("project")} className="btn-base btn-secondary mt-2 w-full">Run project review</button>
                </div>
                <div>
                  <input className="input" value={aiJobId} onChange={(event) => setAiJobId(event.target.value)} placeholder="Job ID for portfolio match" />
                  <button disabled={Boolean(aiBusy)} onClick={() => void runAI("match")} className="btn-base btn-secondary mt-2 w-full">Run job match</button>
                </div>
              </div>
              {latestAI && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-5">
                  <div>
                    <h3 className="text-sm font-medium">Latest summary</h3>
                    <p className="text-sm text-muted-foreground mt-2">{latestAI.summary}</p>
                    <div className="flex flex-wrap gap-1.5 mt-3">
                      {latestAI.technology_stack.slice(0, 10).map((tech) => <span key={tech} className="tag">{tech}</span>)}
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium">Next actions</h3>
                    <ul className="mt-2 space-y-1">
                      {latestAI.action_items.slice(0, 4).map((item) => (
                        <li key={item.action} className="text-sm text-muted-foreground">{item.priority}: {item.action}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
              <div className="mt-5">
                <h3 className="text-sm font-medium">Growth timeline</h3>
                {aiHistory.length === 0 && <p className="text-sm text-muted-foreground mt-2">No portfolio AI reviews yet.</p>}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-3">
                  {aiHistory.slice(0, 6).map((review) => (
                    <div key={review.id} className="border border-border rounded-lg p-3">
                      <p className="text-sm font-medium">{review.review_type.replace("_", " ")} - {review.overall_score}/100</p>
                      <p className="text-xs text-muted-foreground mt-1">{new Date(review.created_at).toLocaleString()}</p>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="lg:col-span-3 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="border border-border rounded-xl bg-card p-5">
                <h2 className="font-semibold mb-4">Skills and languages</h2>
                <div className="flex flex-wrap gap-1.5">{portfolio.skills.map((skill) => <span key={skill.id} className="tag">{skill.name}</span>)}</div>
              </div>
              <div className="border border-border rounded-xl bg-card p-5">
                <h2 className="font-semibold mb-4">Projects and achievements</h2>
                <div className="space-y-4">
                  {portfolio.projects.map((project) => (
                    <article key={project.id} className="border border-border rounded-lg p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-medium">{project.title}</p>
                          <p className="text-xs text-muted-foreground">{project.tech_stack.join(", ") || "No technologies listed"}</p>
                        </div>
                        <button onClick={() => void toggleFeatured(project.id, project.is_featured)} className="btn-base btn-secondary text-xs">
                          {project.is_featured ? "Unfeature" : "Feature"}
                        </button>
                      </div>
                      {project.media.length > 0 && (
                        <div className="grid grid-cols-2 gap-2 mt-3">
                          {project.media.map((item) => (
                            <a key={item.id} href={item.url} target="_blank" rel="noreferrer" className="text-xs text-primary truncate">{item.media_type}: {item.title || item.url}</a>
                          ))}
                        </div>
                      )}
                    </article>
                  ))}
                </div>
              </div>
            </section>

            <section className="lg:col-span-3 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="border border-border rounded-xl bg-card p-5">
                <h2 className="font-semibold mb-4">Add project</h2>
                <input className="input" value={projectTitle} onChange={(event) => setProjectTitle(event.target.value)} placeholder="Project title" />
                <input className="input mt-3" value={projectTech} onChange={(event) => setProjectTech(event.target.value)} placeholder="React, Django, SQL" />
                <button onClick={() => void addProject()} className="btn-base btn-primary mt-3">Add project</button>
              </div>
              <div className="border border-border rounded-xl bg-card p-5">
                <h2 className="font-semibold mb-4">Add project media</h2>
                <select className="input" value={mediaProjectId} onChange={(event) => setMediaProjectId(event.target.value)}>
                  <option value="">Choose project</option>
                  {portfolio.projects.map((project) => <option key={project.id} value={project.id}>{project.title}</option>)}
                </select>
                <label className="block mt-3">
                  <span className="text-xs text-muted-foreground">Upload image</span>
                  <input className="input mt-1" type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => setMediaFile(event.target.files?.[0] || null)} />
                </label>
                <input className="input mt-3" value={mediaUrl} onChange={(event) => setMediaUrl(event.target.value)} placeholder="Image or video URL" />
                <button onClick={() => void addMedia()} className="btn-base btn-primary mt-3">Add media</button>
              </div>
            </section>
          </div>
        )}
      </main>
    </>
  );
}
