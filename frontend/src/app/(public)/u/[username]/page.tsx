import { notFound } from "next/navigation";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import type { Metadata } from "next";
import type {
  PublicPortfolio,
  PortfolioSkill,
  PortfolioProject,
  ResumeCertificate,
} from "@/types/careers.types";

const EXPERIENCE_LABELS: Record<string, string> = {
  student: "Student",
  entry: "Entry Level",
  mid: "Mid Level",
  senior: "Senior",
  lead: "Lead / Manager",
};

const SOURCE_COLORS: Record<string, string> = {
  manual: "bg-blue-50 text-blue-700 border-blue-200",
  track: "bg-purple-50 text-purple-700 border-purple-200",
  course: "bg-green-50 text-green-700 border-green-200",
};

async function fetchPortfolio(username: string): Promise<PublicPortfolio | null> {
  try {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/careers/portfolio/${username}/`,
      { next: { revalidate: 300 } }
    );
    if (!res.ok) return null;
    const data = await res.json();
    return data.data || data;
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: { username: string };
}): Promise<Metadata> {
  const portfolio = await fetchPortfolio(params.username);
  if (!portfolio) return { title: "Portfolio not found" };
  return {
    title: `${portfolio.full_name} - T-Career Portfolio`,
    description:
      portfolio.headline ||
      `${portfolio.full_name}'s portfolio on T-Career.`,
    openGraph: {
      title: `${portfolio.full_name} - T-Career Portfolio`,
      description: portfolio.headline,
      type: "profile",
    },
  };
}

function SkillBadge({ skill }: { skill: PortfolioSkill }) {
  const color = SOURCE_COLORS[skill.source] ?? "bg-gray-100 text-gray-700 border-gray-200";
  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${color}`}>
      {skill.name}
    </span>
  );
}

function ProjectCard({ project }: { project: PortfolioProject }) {
  return (
    <div className="border rounded-xl p-5 bg-card space-y-3">
      <div className="flex items-start gap-2 flex-wrap">
        <h3 className="font-semibold text-sm">{project.title}</h3>
        {project.is_featured && (
          <span className="text-xs bg-amber-100 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full">
            Featured
          </span>
        )}
      </div>

      {project.description && (
        <p className="text-sm text-muted-foreground">{project.description}</p>
      )}

      {project.tech_stack.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {project.tech_stack.map((tech) => (
            <span key={tech} className="text-xs bg-secondary text-secondary-foreground px-2 py-0.5 rounded">
              {tech}
            </span>
          ))}
        </div>
      )}

      <div className="flex flex-wrap gap-3">
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
        {project.media?.map((media) => (
          <a key={media.id} href={media.url} target="_blank" rel="noopener noreferrer" className="text-xs text-primary hover:underline">
            {media.is_featured ? "Featured media" : media.media_type}
          </a>
        ))}
      </div>
    </div>
  );
}

function CertificateRow({ cert }: { cert: ResumeCertificate }) {
  return (
    <div className="flex items-center justify-between gap-4 py-2 border-b last:border-0">
      <div>
        <p className="text-sm font-medium">{cert.course_title}</p>
        <p className="text-xs text-muted-foreground mt-0.5">
          {new Date(cert.issued_at).toLocaleDateString("en-US", {
            year: "numeric",
            month: "long",
          })}
        </p>
      </div>
      
       <a href={cert.verify_url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-xs text-primary hover:underline shrink-0"
      >
        Verify
      </a>
    </div>
  );
}

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border rounded-xl p-6 bg-card space-y-4">
      <h2 className="font-semibold text-base">{title}</h2>
      {children}
    </div>
  );
}

export default async function PublicPortfolioPage({
  params,
}: {
  params: { username: string };
}) {
  const portfolio = await fetchPortfolio(params.username);
  if (!portfolio) notFound();

  const skills = portfolio.skills ?? [];
  const projects = portfolio.projects ?? [];
  const featuredProjects = projects.filter((project) => project.is_featured);
  const certificates = portfolio.certificates ?? [];
  const completedCourses = portfolio.completed_courses ?? [];
  const careerTracks = portfolio.career_tracks ?? [];
  const education = portfolio.education ?? [];
  const experience = portfolio.experience ?? [];

  return (
    <>
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

          <div className="md:col-span-1">
            <div className="border rounded-xl p-6 bg-card space-y-4 md:sticky md:top-20">

              <div className="text-center space-y-2">
                {portfolio.avatar_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={portfolio.avatar_url}
                    alt={portfolio.full_name}
                    className="w-16 h-16 rounded-full object-cover border mx-auto"
                  />
                ) : (
                  <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center text-2xl font-bold text-primary mx-auto">
                    {portfolio.full_name?.charAt(0).toUpperCase() ?? "?"}
                  </div>
                )}
                <div>
                  <div className="flex items-center justify-center gap-2">
                    <h1 className="font-bold text-lg">{portfolio.full_name}</h1>
                    {portfolio.is_verified && <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded-full">Verified</span>}
                  </div>
                  {portfolio.username && (
                    <p className="text-xs text-muted-foreground">@{portfolio.username}</p>
                  )}
                </div>
                {portfolio.headline && (
                  <p className="text-sm text-muted-foreground">{portfolio.headline}</p>
                )}
              </div>

              {portfolio.bio && (
                <p className="text-sm text-muted-foreground text-center">{portfolio.bio}</p>
              )}

              <div className="space-y-1 text-sm text-muted-foreground">
                {portfolio.location && <p>{portfolio.location}</p>}
                {portfolio.desired_role && (
                  <p>Looking for: {portfolio.desired_role}</p>
                )}
                <p>{portfolio.open_to_work ? "Open to work" : "Limited availability"}</p>
                {portfolio.experience_level && (
                  <p>{EXPERIENCE_LABELS[portfolio.experience_level]}</p>
                )}
                <p>Remote: {portfolio.remote_preference?.replaceAll("_", " ")}</p>
                <p>Relocation: {portfolio.relocation_willingness?.replaceAll("_", " ")}</p>
              </div>

              {(portfolio.linkedin_url || portfolio.github_url || portfolio.website_url) && (
                <div className="flex flex-col gap-2 pt-2 border-t">
                  {portfolio.linkedin_url && (
                    <a href={portfolio.linkedin_url} target="_blank" rel="noopener noreferrer" className="text-sm text-primary hover:underline">
                      LinkedIn
                    </a>
                  )}
                  {portfolio.github_url && (
                    <a href={portfolio.github_url} target="_blank" rel="noopener noreferrer" className="text-sm text-primary hover:underline">
                      GitHub
                    </a>
                  )}
                  {portfolio.website_url && (
                    <a href={portfolio.website_url} target="_blank" rel="noopener noreferrer" className="text-sm text-primary hover:underline">
                      Website
                    </a>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="md:col-span-2 space-y-6">
            <SectionCard title="About">
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                {portfolio.bio || "This candidate has not added an about section yet."}
              </p>
            </SectionCard>

            {skills.length > 0 && (
              <SectionCard title={`Skills (${skills.length})`}>
                <div className="flex flex-wrap gap-2">
                  {skills.map((skill) => (
                    <SkillBadge key={skill.id} skill={skill} />
                  ))}
                </div>
              </SectionCard>
            )}

            {featuredProjects.length > 0 && (
              <SectionCard title="Featured Projects">
                <div className="space-y-3">
                  {featuredProjects.map((project) => (
                    <ProjectCard key={project.id} project={project} />
                  ))}
                </div>
              </SectionCard>
            )}

            {projects.length > 0 && (
              <SectionCard title={`Projects (${projects.length})`}>
                <div className="space-y-3">
                  {projects.map((project) => (
                    <ProjectCard key={project.id} project={project} />
                  ))}
                </div>
              </SectionCard>
            )}

            {(experience.length > 0 || education.length > 0) && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <SectionCard title="Experience">
                  {experience.length === 0 ? <p className="text-sm text-muted-foreground">No experience listed yet.</p> : experience.map((item) => (
                    <div key={item.id} className="border-b last:border-0 py-2">
                      <p className="text-sm font-medium">{item.title}</p>
                      <p className="text-xs text-muted-foreground">{item.company}</p>
                    </div>
                  ))}
                </SectionCard>
                <SectionCard title="Education">
                  {education.length === 0 ? <p className="text-sm text-muted-foreground">No education listed yet.</p> : education.map((item) => (
                    <div key={item.id} className="border-b last:border-0 py-2">
                      <p className="text-sm font-medium">{item.degree || item.field || "Education"}</p>
                      <p className="text-xs text-muted-foreground">{item.institution}</p>
                    </div>
                  ))}
                </SectionCard>
              </div>
            )}

            {certificates.length > 0 && (
              <SectionCard title={`Certificates (${certificates.length})`}>
                <div>
                  {certificates.map((cert) => (
                    <CertificateRow key={cert.cert_number} cert={cert} />
                  ))}
                </div>
              </SectionCard>
            )}

            {careerTracks.length > 0 && (
              <SectionCard title="Career Tracks">
                <div className="space-y-3">
                  {careerTracks.map((track) => (
                    <div key={track.track_slug}>
                      <div className="flex items-center justify-between mb-1">
                        <Link href={`/tracks/${track.track_slug}`} className="text-sm font-medium hover:text-primary transition-colors">
                          {track.track_title}
                        </Link>
                        <div className="flex items-center gap-2">
                          {track.is_completed && (
                            <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded-full">
                              Completed
                            </span>
                          )}
                          <span className="text-xs text-muted-foreground">
                            {track.progress_percentage}%
                          </span>
                        </div>
                      </div>
                      <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all"
                          style={{
                            width: `${track.progress_percentage}%`,
                            backgroundColor: track.track_color,
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </SectionCard>
            )}

            {completedCourses.length > 0 && (
              <SectionCard title={`Completed Courses (${completedCourses.length})`}>
                <div>
                  {completedCourses.map((course) => (
                    <div key={course.slug} className="flex items-center justify-between py-2 border-b last:border-0">
                      <Link href={`/courses/${course.slug}`} className="text-sm hover:text-primary transition-colors">
                        {course.title}
                      </Link>
                      <span className="text-xs text-muted-foreground capitalize">
                        {course.level}
                      </span>
                    </div>
                  ))}
                </div>
              </SectionCard>
            )}

            {skills.length === 0 && projects.length === 0 && certificates.length === 0 && experience.length === 0 && education.length === 0 && (
              <div className="border rounded-xl p-8 text-center text-muted-foreground">
                <p>This public career profile is just getting started.</p>
              </div>
            )}

          </div>
        </div>
      </main>
    </>
  );
}
