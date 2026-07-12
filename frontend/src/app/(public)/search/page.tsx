"use client";
import { Suspense } from "react";

import { useState, useEffect, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import api from "@/lib/api/client";

interface SearchResults {
  query: string;
  total: number;
  courses: { id: string; title: string; slug: string; short_description: string; level: string; price: string; instructor_name: string; }[];
  tracks: { id: string; title: string; slug: string; short_description: string; color: string; duration_display: string; }[];
  jobs: { id: string; title: string; company_name: string; location: string; job_type_display: string; salary_display: string; }[];
}

function SearchForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [query, setQuery] = useState(searchParams.get("q") || "");
  const [results, setResults] = useState<SearchResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"all" | "course" | "track" | "job">("all");

  const doSearch = useCallback(async (q: string, type: string) => {
    if (!q || q.length < 2) return;
    setLoading(true);
    try {
      const res = await api.get(`/search/?q=${encodeURIComponent(q)}&type=${type}&limit=10`);
      const data = res.data.data || res.data;
      setResults(data);
    } catch {
      setResults(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const q = searchParams.get("q");
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (q) { doSearch(q, activeTab); }
  }, [searchParams, activeTab, doSearch]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (query.trim()) router.push(`/search?q=${encodeURIComponent(query.trim())}`);
  }

  const courseCount = results?.courses?.length ?? 0;
  const trackCount = results?.tracks?.length ?? 0;
  const jobCount = results?.jobs?.length ?? 0;
  const totalCount = results?.total ?? 0;

  return (
    <>
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 py-8">
        <form onSubmit={handleSearch} className="mb-6">
          <div className="flex gap-3">
            <input type="text" value={query} onChange={(e) => setQuery(e.target.value)}
              placeholder="Search courses, tracks, jobs..."
              className="flex-1 border rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 bg-background" autoFocus />
            <button type="submit" className="bg-primary text-primary-foreground px-6 py-3 rounded-xl text-sm font-medium hover:bg-primary/90 transition-colors">Search</button>
          </div>
        </form>

        {results && (
          <>
            <div className="flex gap-2 mb-6 border-b">
              {([
                { key: "all", label: "All", count: totalCount },
                { key: "course", label: "Courses", count: courseCount },
                { key: "track", label: "Tracks", count: trackCount },
                { key: "job", label: "Jobs", count: jobCount },
              ] as const).map((tab) => (
                <button key={tab.key} onClick={() => setActiveTab(tab.key)}
                  className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === tab.key ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"}`}>
                  {tab.label}{tab.count > 0 && <span className="ml-1.5 text-xs bg-muted px-1.5 py-0.5 rounded-full">{tab.count}</span>}
                </button>
              ))}
            </div>

            {loading ? (
              <div className="space-y-3">{[...Array(5)].map((_, i) => <div key={i} className="h-20 bg-muted rounded-xl animate-pulse" />)}</div>
            ) : totalCount === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <p className="mb-2">No results for &quot;{results.query}&quot;</p>
                <p className="text-sm">Try different keywords or browse the catalog.</p>
              </div>
            ) : (
              <div className="space-y-6">
                {(activeTab === "all" || activeTab === "course") && courseCount > 0 && (
                  <section>
                    {activeTab === "all" && <h2 className="font-semibold mb-3">Courses</h2>}
                    <div className="space-y-2">
                      {results.courses.map((course) => (
                        <Link key={course.id} href={`/courses/${course.slug}`}
                          className="flex items-start gap-4 p-4 border rounded-xl hover:shadow-sm transition-shadow bg-card">
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm">{course.title}</p>
                            <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">{course.short_description}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-xs text-muted-foreground capitalize">{course.level}</span>
                              <span className="text-xs text-muted-foreground">{course.instructor_name}</span>
                            </div>
                          </div>
                          <span className="text-sm font-medium text-primary flex-shrink-0">
                            {parseFloat(course.price) === 0 ? "Free" : `$${course.price}`}
                          </span>
                        </Link>
                      ))}
                    </div>
                  </section>
                )}

                {(activeTab === "all" || activeTab === "track") && trackCount > 0 && (
                  <section>
                    {activeTab === "all" && <h2 className="font-semibold mb-3">Career Tracks</h2>}
                    <div className="space-y-2">
                      {results.tracks.map((track) => (
                        <Link key={track.id} href={`/tracks/${track.slug}`}
                          className="flex items-center gap-4 p-4 border rounded-xl hover:shadow-sm transition-shadow bg-card">
                          <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold flex-shrink-0"
                            style={{ backgroundColor: track.color }}>{track.title.charAt(0)}</div>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm">{track.title}</p>
                            <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">{track.short_description}</p>
                          </div>
                          <span className="text-xs text-muted-foreground flex-shrink-0">{track.duration_display}</span>
                        </Link>
                      ))}
                    </div>
                  </section>
                )}

                {(activeTab === "all" || activeTab === "job") && jobCount > 0 && (
                  <section>
                    {activeTab === "all" && <h2 className="font-semibold mb-3">Jobs</h2>}
                    <div className="space-y-2">
                      {results.jobs.map((job) => (
                        <Link key={job.id} href="/jobs"
                          className="flex items-start justify-between gap-4 p-4 border rounded-xl hover:shadow-sm transition-shadow bg-card">
                          <div>
                            <p className="font-medium text-sm">{job.title}</p>
                            <p className="text-xs text-muted-foreground mt-0.5">{job.company_name} - {job.location}</p>
                          </div>
                          <div className="text-right flex-shrink-0">
                            <p className="text-xs text-muted-foreground">{job.job_type_display}</p>
                            <p className="text-xs text-primary font-medium">{job.salary_display}</p>
                          </div>
                        </Link>
                      ))}
                    </div>
                  </section>
                )}
              </div>
            )}
          </>
        )}

        {!results && !loading && (
          <div className="text-center py-16 text-muted-foreground">
            <p className="text-lg mb-2">What are you looking for?</p>
            <p className="text-sm">Search courses, career tracks, and job listings.</p>
          </div>
        )}
      </main>
    </>
  );
}

export default function SearchPage() { return <Suspense><SearchForm /></Suspense>; }
