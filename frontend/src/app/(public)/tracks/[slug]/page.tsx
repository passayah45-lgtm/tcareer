import { notFound } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { TrackEnrollSection } from "@/components/tracks/TrackEnrollSection";
import { formatTrackFee } from "@/lib/track-pricing";
import type { CareerTrack } from "@/types/track.types";

export const dynamic = "force-dynamic";

async function fetchTrack(slug: string): Promise<CareerTrack | null> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) return null;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);
  try {
    const res = await fetch(
      `${apiUrl}/tracks/${slug}/`,
      { next: { revalidate: 120 }, signal: controller.signal }
    );
    if (!res.ok) return null;
    const data = await res.json();
    return (data.data ?? data) as CareerTrack;
  } catch {
    return null;
  } finally {
    clearTimeout(timeout);
  }
}

export default async function TrackDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const track = await fetchTrack(slug);
  if (!track) notFound();

  return (
    <>
      <Navbar />
      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Left: Track info */}
          <div className="lg:col-span-2 space-y-6">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center text-white text-xl font-bold"
                  style={{ backgroundColor: track.color }}
                >
                  {track.title.charAt(0)}
                </div>
                <div>
                  <span className="text-xs text-muted-foreground capitalize">
                    {track.category_display}
                  </span>
                  <h1 className="text-2xl font-bold">{track.title}</h1>
                </div>
              </div>
              <p className="text-muted-foreground">{track.short_description}</p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                { label: "Courses", value: String(track.required_courses_count) },
                { label: "Duration", value: track.duration_display },
                { label: "Track Fee", value: formatTrackFee(track) },
                { label: "Level", value: track.difficulty.charAt(0).toUpperCase() + track.difficulty.slice(1) },
              ].map((stat) => (
                <div key={stat.label} className="border rounded-xl p-3 text-center">
                  <p className="text-sm font-semibold">{stat.value}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{stat.label}</p>
                </div>
              ))}
            </div>

            {/* Skills */}
            {track.skills_acquired.length > 0 && (
              <div>
                <h2 className="font-semibold mb-3">Skills you will gain</h2>
                <div className="flex flex-wrap gap-2">
                  {track.skills_acquired.map((skill) => (
                    <span
                      key={skill}
                      className="text-xs border rounded-full px-3 py-1 bg-muted"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Job titles */}
            {track.target_job_titles.length > 0 && (
              <div>
                <h2 className="font-semibold mb-3">Target job titles</h2>
                <div className="flex flex-wrap gap-2">
                  {track.target_job_titles.map((title) => (
                    <span
                      key={title}
                      className="text-xs bg-primary/10 text-primary rounded-full px-3 py-1"
                    >
                      {title}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Course roadmap by stage */}
            {track.courses_by_stage && track.courses_by_stage.length > 0 && (
              <div>
                <h2 className="font-semibold mb-4">Learning roadmap</h2>
                <div className="space-y-6">
                  {track.courses_by_stage.map((stageGroup) => (
                    <div key={stageGroup.stage}>
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-bold">
                          {stageGroup.stage}
                        </div>
                        <h3 className="font-medium text-sm">
                          Stage {stageGroup.stage}: {stageGroup.stage_name}
                        </h3>
                      </div>
                      <div className="ml-8 space-y-2">
                        {stageGroup.courses.map((tc) => (
                          <div
                            key={tc.id}
                            className="flex items-center gap-3 p-3 border rounded-lg bg-card"
                          >
                            <div
                              className={`w-4 h-4 rounded-full flex-shrink-0 ${
                                tc.is_course_completed
                                  ? "bg-primary"
                                  : "bg-muted border-2 border-muted-foreground/30"
                              }`}
                            />
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium truncate">
                                {tc.course_title}
                              </p>
                              <p className="text-xs text-muted-foreground capitalize">
                                {tc.course_level} level
                              </p>
                            </div>
                            {!tc.is_required && (
                              <span className="text-xs text-muted-foreground flex-shrink-0">
                                Optional
                              </span>
                            )}
                            {tc.is_course_completed && (
                              <span className="text-xs text-primary flex-shrink-0">
                                Done
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right: Enroll card */}
          <div className="lg:col-span-1">
            <TrackEnrollSection track={track} />
          </div>

        </div>
      </main>
    </>
  );
}
