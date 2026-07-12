"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { useAuthStore } from "@/stores/auth.store";
import { toast } from "@/components/shared/Toast";
import { getMyPortfolio, syncSkills } from "@/lib/api/careers.api";
import type { Portfolio, PortfolioSkill, PortfolioProject } from "@/types/careers.types";

const EXPERIENCE_LABELS: Record<string, string> = {
  student: "Student",
  entry: "Entry Level",
  mid: "Mid Level",
  senior: "Senior",
  lead: "Lead / Manager",
};

const VISIBILITY_LABELS: Record<string, string> = {
  public: "Public",
  unlisted: "Unlisted",
  private: "Private",
};

const VISIBILITY_COLORS: Record<string, string> = {
  public: "bg-green-100 text-green-700",
  unlisted: "bg-yellow-100 text-yellow-700",
  private: "bg-gray-100 text-gray-600",
};

function StatCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="border rounded-xl p-4 bg-card text-center">
      <p className="text-2xl font-bold text-primary">{value}</p>
      <p className="text-xs text-muted-foreground mt-1">{label}</p>
    </div>
  );
}

function SkillBadge({ skill }: { skill: PortfolioSkill }) {
  const sourceColors: Record<string, string> = {
    manual: "bg-blue-50 text-blue-700 border-blue-200",
    track: "bg-purple-50 text-purple-700 border-purple-200",
    course: "bg-green-50 text-green-700 border-green-200",
  };

  return (
    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium border ${sourceColors[skill.source] ?? "bg-gray-100 text-gray-700 border-gray-200"}`}>
      {skill.name}
      {skill.category && <span className="opacity-60">- {skill.category}</span>}
    </span>
  );
}

function ProjectCard({ project }: { project: PortfolioProject }) {
  return (
    <div className="border rounded-xl p-5 bg-card space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-sm">{project.title}</h3>
            {project.is_featured && (
              <span className="text-xs bg-amber-100 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full">
                Featured
              </span>
            )}
          </div>
          {project.description && (
            <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
              {project.description}
            </p>
          )}
        </div>
      </div>

      {project.tech_stack.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {project.tech_stack.map((tech) => (
            <span key={tech} className="text-xs bg-secondary text-secondary-foreground px-2 py-0.5 rounded">
              {tech}
            </span>
          ))}
        </div>
      )}

      <div className="flex flex-wrap gap-3 pt-1">
        {project.project_url && (
          <a href={project.project_url} target="_blank" rel="noopener noreferrer" className="text-xs text-primary hover:underline">
            Live demo
          </a>
        )}
        {project.github_url && (
          <a href={project.github_url} target="_blank" rel="noopener noreferrer" className="text-xs text-primary hover:underline">
            GitHub
          </a>
        )}
        {project.demo_video_url && (
          <a href={project.demo_video_url} target="_blank" rel="noopener noreferrer" className="text-xs text-primary hover:underline">
            Demo video
          </a>
        )}
      </div>

      {(project.start_date || project.end_date) && (
        <p className="text-xs text-muted-foreground">
          {project.start_date ?? ""}
          {project.start_date && project.end_date ? " - " : ""}
          {project.end_date ?? ""}
        </p>
      )}
    </div>
  );
}

function SectionCard({
  title,
  action,
  children,
}: {
  title: string;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="border rounded-xl p-6 bg-card space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-base">{title}</h2>
        {action}
      </div>
      {children}
    </div>
  );
}

export default function PortfolioPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  const fetchPortfolio = useCallback(async () => {
    try {
      const data = await getMyPortfolio();
      setPortfolio(data);
    } catch {
      toast("Failed to load portfolio.", "error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchPortfolio();
  }, [fetchPortfolio, isAuthenticated, router]);

  async function handleSync() {
    setSyncing(true);
    try {
      const result = await syncSkills();
      const added = result.total_added;
      if (added === 0) {
        toast("No new skills to sync.", "info");
      } else {
        toast(`Synced ${added} new skill${added === 1 ? "" : "s"} from your courses and tracks.`, "success");
      }
      await fetchPortfolio();
    } catch {
      toast("Skill sync failed.", "error");
    } finally {
      setSyncing(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="max-w-4xl mx-auto px-4 py-10">
          <div className="space-y-4 animate-pulse">
            <div className="h-8 w-48 bg-muted rounded" />
            <div className="h-40 bg-muted rounded-xl" />
            <div className="h-40 bg-muted rounded-xl" />
          </div>
        </main>
      </div>
    );
  }

  if (!portfolio) return null;

  const completedLinks = [
    portfolio.linkedin_url,
    portfolio.github_url,
    portfolio.website_url,
  ].filter(Boolean).length;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 py-10 space-y-6">

        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">My Portfolio</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Your public career profile for recruiters and employers.
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {portfolio.public_url && portfolio.visibility !== "private" && (
              <a href={portfolio.public_url} target="_blank" rel="noopener noreferrer" className="text-sm text-primary hover:underline">
                View public page
              </a>
            )}
            <button
              onClick={() => router.push("/portfolio/edit")}
              className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
            >
              Edit portfolio
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatCard label="Skills" value={portfolio.skills.length} />
          <StatCard label="Projects" value={portfolio.projects.length} />
          <StatCard label="Profile views" value={portfolio.profile_views} />
          <StatCard label="Links added" value={`${completedLinks}/3`} />
        </div>

        <SectionCard title="Profile">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              {portfolio.avatar_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={portfolio.avatar_url} alt={portfolio.full_name} className="w-14 h-14 rounded-full object-cover border" />
              ) : (
                <div className="w-14 h-14 rounded-full bg-muted flex items-center justify-center text-lg font-semibold text-muted-foreground">
                  {portfolio.full_name?.[0] ?? "?"}
                </div>
              )}
              <div>
                <p className="font-semibold">{portfolio.full_name}</p>
                {portfolio.username && (
                  <p className="text-xs text-muted-foreground">@{portfolio.username}</p>
                )}
              </div>
              <span className={`ml-auto text-xs px-2 py-1 rounded-full font-medium ${VISIBILITY_COLORS[portfolio.visibility]}`}>
                {VISIBILITY_LABELS[portfolio.visibility]}
              </span>
            </div>

            {portfolio.headline && <p className="text-sm font-medium">{portfolio.headline}</p>}
            {portfolio.bio && <p className="text-sm text-muted-foreground">{portfolio.bio}</p>}

            <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
              {portfolio.location && <span>{portfolio.location}</span>}
              {portfolio.desired_role && <span>Looking for: {portfolio.desired_role}</span>}
              {portfolio.experience_level && <span>{EXPERIENCE_LABELS[portfolio.experience_level]}</span>}
            </div>

            {(portfolio.linkedin_url || portfolio.github_url || portfolio.website_url) && (
              <div className="flex flex-wrap gap-3 pt-1">
                {portfolio.linkedin_url && (
                  <a href={portfolio.linkedin_url} target="_blank" rel="noopener noreferrer" className="text-xs text-primary hover:underline">
                    LinkedIn
                  </a>
                )}
                {portfolio.github_url && (
                  <a href={portfolio.github_url} target="_blank" rel="noopener noreferrer" className="text-xs text-primary hover:underline">
                    GitHub
                  </a>
                )}
                {portfolio.website_url && (
                  <a href={portfolio.website_url} target="_blank" rel="noopener noreferrer" className="text-xs text-primary hover:underline">
                    Website
                  </a>
                )}
              </div>
            )}

            {!portfolio.headline && !portfolio.bio && !portfolio.desired_role && (
              <p className="text-sm text-muted-foreground italic">
                Your profile is empty. Add a headline and bio so recruiters know who you are.
              </p>
            )}
          </div>
        </SectionCard>

        <SectionCard
          title={`Skills (${portfolio.skills.length})`}
          action={
            <button
              onClick={handleSync}
              disabled={syncing}
              className="text-xs px-3 py-1.5 rounded-lg border hover:bg-muted transition-colors disabled:opacity-50"
            >
              {syncing ? "Syncing..." : "Sync from courses"}
            </button>
          }
        >
          {portfolio.skills.length === 0 ? (
            <div className="text-center py-6 text-sm text-muted-foreground">
              <p>No skills yet.</p>
              <p className="mt-1">
                Add skills manually or sync them from your completed courses.
              </p>
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {portfolio.skills.map((skill) => (
                <SkillBadge key={skill.id} skill={skill} />
              ))}
            </div>
          )}
        </SectionCard>

        <SectionCard title={`Projects (${portfolio.projects.length})`}>
          {portfolio.projects.length === 0 ? (
            <div className="text-center py-6 text-sm text-muted-foreground">
              <p>No projects yet.</p>
              <p className="mt-1">
                Add projects to show recruiters what you have built.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {portfolio.projects.map((project) => (
                <ProjectCard key={project.id} project={project} />
              ))}
            </div>
          )}
        </SectionCard>

        {portfolio.public_url && (
          <div className="border rounded-xl p-5 bg-card flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-medium">Your public portfolio link</p>
              <p className="text-xs text-muted-foreground mt-0.5 break-all">
                {portfolio.public_url}
              </p>
            </div>
            <button
              onClick={() => {
                navigator.clipboard.writeText(portfolio.public_url!);
                toast("Link copied to clipboard.", "success");
              }}
              className="shrink-0 text-xs px-3 py-1.5 rounded-lg border hover:bg-muted transition-colors"
            >
              Copy link
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
